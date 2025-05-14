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

    def get_token(self):
        if (self.access_token and self.token_expiration and 
            datetime.now() < self.token_expiration - timedelta(minutes=5)):
            return True
            
        try:
            response = requests.post(
                f"{self.api_url}/token",
                data={
                    "username": self.api_username,
                    "password": self.api_password,
                    "grant_type": "password"
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiration = datetime.now() + timedelta(minutes=30)
            print("Token obtido com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao obter token: {str(e)}")
            return False

    def get_ips_from_api(self):
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
                        ips.append((src_ip, ataque[0]))  # Include flow_id
            
            print(f"Encontrados {len(ips)} IPs de ataques")
            return ips

        except Exception as e:
            print(f"Erro ao obter IPs: {str(e)}")
            return []

    def execute_ansible_playbook(self, flow_id):
        try:
            print("Executando playbook Ansible...")
            process = subprocess.run(
                [
                    "ansible-playbook",
                    "rules_playbook.yml",
                    "-i", "Api_watchdog/dynamic_inventory.py"
                ],
                capture_output=True,
                text=True
            )

            print(process.stdout)
            if process.stderr:
                print(f"Erro: {process.stderr}")

            if process.returncode == 0:
                self.mark_attack_as_resolved(flow_id)

            return process.returncode == 0

        except Exception as e:
            print(f"Erro ao executar playbook: {str(e)}")
            return False

    def mark_attack_as_resolved(self, flow_id):
        try:
            api_url = f"http://164.72.15.30:5050/dados/ataques/processar/{flow_id}"
            response = requests.put(api_url)

            if response.status_code == 200:
                print(f"Ataque {flow_id} marcado como processado com sucesso!")
            else:
                print(f"Falha ao marcar ataque {flow_id} como processado. Status: {response.status_code}")

        except Exception as e:
            print(f"Erro ao marcar ataque como processado: {str(e)}")

    def run(self):
        print("Iniciando serviço de monitoramento...")
        
        while True:
            try:
                ips = self.get_ips_from_api()
                
                if ips:
                    print(f"Novos IPs detectados: {ips}")
                    for ip, flow_id in ips:
                        print(f"Processando IP: {ip} com flow_id: {flow_id}")
                        if self.execute_ansible_playbook(flow_id):
                            print("Mitigação aplicada com sucesso")
                        else:
                            print("Falha ao aplicar mitigação")
                
                time.sleep(self.check_interval)
        
            except Exception as e:
                print(f"Erro no loop principal: {str(e)}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()
