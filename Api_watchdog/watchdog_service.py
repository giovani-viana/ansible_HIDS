#!/usr/bin/env python3
import requests
import time
import subprocess
import logging
from datetime import datetime
import os
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)

class AnsibleWatchdog:
    def __init__(self):
        # Configurações da API
        self.api_url = os.getenv("API_URL", "http://localhost:5000")
        self.username = os.getenv("API_USERNAME", "seu_usuario")
        self.password = os.getenv("API_PASSWORD", "sua_senha")
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 minutos
        self.last_ips = set()
        self.access_token = None

    def get_token(self):
        """Obtém o token de autenticação"""
        try:
            response = requests.post(
                f"{self.api_url}/token",
                data={
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password"  # Necessário para OAuth2PasswordRequestForm
                }
            )
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            logging.info("Token de autenticação obtido com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao obter token de autenticação: {str(e)}")
            return False

    def get_ips_from_api(self):
        """Obtém IPs de ataques da API"""
        try:
            # Verifica se precisa renovar o token
            if not self.access_token and not self.get_token():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_url}/dados/ataques/novos",
                headers=headers,
                timeout=30
            )
            
            # Se o token expirou, tenta renovar
            if response.status_code == 401:
                if not self.get_token():
                    return None
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    f"{self.api_url}/dados/ataques/novos",
                    headers=headers,
                    timeout=30
                )

            response.raise_for_status()
            ataques = response.json().get("dados", [])
            
            if not ataques:
                logging.info("Nenhum novo ataque detectado")
                return set()

            # Extrai os IPs de origem dos ataques (índice 1 é o src_ip)
            ips = set()
            for ataque in ataques:
                if len(ataque) > 1:  # Verifica se há dados suficientes
                    flow_id = ataque[0]  # flow_id está no índice 0
                    src_ip = ataque[1]   # src_ip está no índice 1
                    ips.add(src_ip)
                    
                    # Marca o ataque como processado
                    self.marcar_ataque_processado(flow_id)
            
            logging.info(f"Encontrados {len(ips)} IPs únicos de ataques")
            return ips

        except Exception as e:
            logging.error(f"Erro ao obter IPs da API: {str(e)}")
            return None

    def marcar_ataque_processado(self, flow_id):
        """Marca um ataque como processado na API"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.put(
                f"{self.api_url}/dados/ataques/processar/{flow_id}",
                headers=headers
            )
            response.raise_for_status()
            logging.info(f"Ataque {flow_id} marcado como processado")
        except Exception as e:
            logging.error(f"Erro ao marcar ataque {flow_id} como processado: {str(e)}")

    def execute_ansible_playbook(self):
        """Executa o playbook Ansible"""
        try:
            logging.info("Executando playbook Ansible...")
            # Passa os IPs como variável extra para o playbook
            ips_str = ','.join(self.last_ips)
            result = subprocess.run(
                [
                    "ansible-playbook",
                    "rules_playbook.yml",
                    "-e", f"target_ips={ips_str}"
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logging.info("Playbook executado com sucesso")
            else:
                logging.error(f"Erro na execução do playbook: {result.stderr}")
        except Exception as e:
            logging.error(f"Erro ao executar playbook: {str(e)}")

    def run(self):
        """Loop principal do watchdog"""
        logging.info("Iniciando serviço de monitoramento...")
        
        while True:
            try:
                current_ips = self.get_ips_from_api()
                
                if current_ips is not None and current_ips != self.last_ips:
                    logging.info(f"Detectada mudança na lista de IPs")
                    logging.info(f"IPs anteriores: {self.last_ips}")
                    logging.info(f"Novos IPs: {current_ips}")
                    
                    if current_ips:  # Só executa se houver IPs para processar
                        self.last_ips = current_ips
                        self.execute_ansible_playbook()
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logging.error(f"Erro no loop principal: {str(e)}")
                time.sleep(60)  # Espera 1 minuto antes de tentar novamente

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()