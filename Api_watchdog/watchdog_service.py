#!/usr/bin/env python3
import requests
import time
import subprocess
import os
from datetime import datetime, timedelta

class AnsibleWatchdog:
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'http://164.72.15.30:5050')
        self.api_username = os.getenv('API_USERNAME', 'hids')
        self.api_password = os.getenv('API_PASSWORD', 'hids')
        self.access_token = None
        self.token_expiration = None
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '15'))
        self.max_retries = 3  # Número máximo de tentativas
        self.retry_delay = 5  # Segundos entre tentativas

    def get_token(self):
        """Obtém token de autenticação com tratamento robusto de erros"""
        try:
            # Se temos um token válido, retorna True
            if (self.access_token and self.token_expiration and 
                datetime.now() < self.token_expiration - timedelta(minutes=5)):
                return True
                
            response = requests.post(
                f"{self.api_url}/token",
                data={
                    "username": self.api_username,
                    "password": self.api_password,
                    "grant_type": "password"
                },
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiration = datetime.now() + timedelta(seconds=token_data.get("expires_in", 1800))
            print("Token obtido com sucesso")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter token: {str(e)}")
            self.access_token = None
            self.token_expiration = None
            return False

    def make_authenticated_request(self, method, endpoint, **kwargs):
        """Faz requisições autenticadas com tratamento de token expirado"""
        for attempt in range(self.max_retries):
            if not self.get_token():
                print("Falha ao obter token de autenticação")
                return None
                
            headers = kwargs.get('headers', {})
            headers.update({"Authorization": f"Bearer {self.access_token}"})
            kwargs['headers'] = headers
            
            try:
                response = requests.request(
                    method,
                    f"{self.api_url}{endpoint}",
                    **kwargs
                )
                
                # Se token expirou, tentamos renovar uma vez
                if response.status_code == 401 and attempt == 0:
                    print("Token expirado, tentando renovar...")
                    self.access_token = None
                    continue
                    
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição (tentativa {attempt + 1}): {str(e)}")
                time.sleep(self.retry_delay)
                
        return None

    def get_ips_from_api(self):
        """Obtém os IPs de ataques da API"""
        if not self.access_token and not self.get_token():
            return []

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_url}/dados/ataques/novos",
                headers=headers,
                timeout=30
            )

            if response.status_code == 401:
                if not self.get_token():
                    return []
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    f"{self.api_url}/dados/ataques/novos",
                    headers=headers,
                    timeout=30
                )

            response.raise_for_status()
            ataques = response.json().get("dados", [])

            if not ataques:
                print("Nenhum novo ataque detectado")
                return []

            ips = []
            for ataque in ataques:
                if len(ataque) > 1:
                    src_ip = ataque[1]
                    if src_ip != "0.0.0.0":
                        ips.append((src_ip, ataque[0]))  # Inclui flow_id

            print(f"Encontrados {len(ips)} IPs de ataques")
            return ips

        except Exception as e:
            print(f"Erro ao obter IPs: {str(e)}")
            return []

    def mark_attack_as_resolved(self, flow_id):
        """Marca ataque como processado com tratamento robusto"""
        for attempt in range(self.max_retries):
            print(f"Tentando marcar ataque {flow_id} como processado (tentativa {attempt + 1})")
            
            response = self.make_authenticated_request(
                'PUT',
                f"/dados/ataques/processar/{flow_id}"
            )
            
            if response is None:
                print("Falha na comunicação com a API")
                continue
                
            if response.status_code == 200:
                print(f"Ataque {flow_id} marcado como processado com sucesso!")
                return True
            elif response.status_code == 403:
                print(f"Permissão negada para marcar ataque {flow_id}. Verifique credenciais.")
                return False
            else:
                print(f"Resposta inesperada ao marcar ataque {flow_id}. Status: {response.status_code}")
                
            time.sleep(self.retry_delay)
            
        print(f"Falha ao marcar ataque {flow_id} como processado após {self.max_retries} tentativas")
        return False

    def execute_ansible_playbook(self, flow_id):
        """Executa playbook ansible com melhor tratamento de erros"""
        try:
            print("Executando playbook Ansible...")
            process = subprocess.run(
                [
                    "ansible-playbook",
                    "rules_playbook.yml",
                    "-i", "Api_watchdog/dynamic_inventory.py"
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos de timeout
            )

            if process.stdout:
                print("Saída do Ansible:\n" + process.stdout)
            if process.stderr:
                print("Erros do Ansible:\n" + process.stderr)

            return process.returncode == 0

        except subprocess.TimeoutExpired:
            print("Playbook Ansible excedeu o tempo limite")
            return False
        except Exception as e:
            print(f"Erro inesperado ao executar playbook: {str(e)}")
            return False

    def process_attack(self, ip, flow_id):
        """Processa um ataque individual com fluxo melhorado"""
        print(f"Processando IP: {ip} com flow_id: {flow_id}")
        
        # Primeiro aplica a mitigação
        if not self.execute_ansible_playbook(flow_id):
            print("Falha ao aplicar mitigação")
            return False
            
        print("Mitigação aplicada com sucesso")
        
        # Só marca como resolvido se a mitigação foi bem-sucedida
        if self.mark_attack_as_resolved(flow_id):
            return True
            
        print("Mitigação aplicada mas falha ao marcar como resolvido")
        return False

    def run(self):
        """Loop principal com tratamento de erros robusto"""
        print("Iniciando serviço de monitoramento...")

        while True:
            try:
                ips = self.get_ips_from_api()

                if ips:
                    print(f"Novos IPs detectados: {ips}")
                    for ip, flow_id in ips:
                        self.process_attack(ip, flow_id)

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"Erro crítico no loop principal: {str(e)}")
                time.sleep(self.check_interval * 2)  # Espera mais tempo após erro crítico

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()