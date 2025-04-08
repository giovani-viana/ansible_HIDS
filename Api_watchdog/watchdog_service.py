#!/usr/bin/env python3
import requests
import time
import subprocess
import logging
from datetime import datetime

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
        self.api_url = "http://sua-api.com/ips" #adicionar endereço da api
        self.check_interval = 300  # 5 minutos
        self.last_ips = set()

    def get_ips_from_api(self):
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            return set(response.json())
        except Exception as e:
            logging.error(f"Erro ao obter IPs da API: {str(e)}")
            return None

    def execute_ansible_playbook(self):
        try:
            logging.info("Executando playbook Ansible...")
            result = subprocess.run(
                ["ansible-playbook", "rules_playbook.yml"],
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
        logging.info("Iniciando serviço de monitoramento...")
        
        while True:
            current_ips = self.get_ips_from_api()
            
            if current_ips is not None and current_ips != self.last_ips:
                logging.info(f"Detectada mudança na lista de IPs")
                logging.info(f"IPs anteriores: {self.last_ips}")
                logging.info(f"Novos IPs: {current_ips}")
                
                self.execute_ansible_playbook()
                self.last_ips = current_ips
            
            time.sleep(self.check_interval)

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()