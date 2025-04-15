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
        # Configurações da API através de variáveis de ambiente do Docker
        self.api_url = os.environ['API_URL']
        self.username = os.environ['API_USERNAME']
        self.password = os.environ['API_PASSWORD']
        self.check_interval = int(os.environ['CHECK_INTERVAL'])
        self.last_ips = set()
        self.access_token = None

        # Log das configurações (sem mostrar a senha)
        logging.info(f"Configurações carregadas:")
        logging.info(f"API URL: {self.api_url}")
        logging.info(f"Username: {self.username}")
        logging.info(f"Check Interval: {self.check_interval} segundos")

    def get_token(self):
        """Obtém o token de autenticação"""
        try:
            response = requests.post(
                f"{self.api_url}/token",
                data={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            logging.info("Token de autenticação obtido com sucesso")
        except Exception as e:
            logging.error(f"Erro ao obter token de autenticação: {str(e)}")
            return False
        return True

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
            dados = response.json()["dados"]
            
            if not dados:
                logging.info("Nenhum novo ataque detectado")
                return set()
            
            # Extrai apenas os IPs de origem dos ataques
            ips = set(ataque[1] for ataque in dados)  # src_ip é o segundo campo
            
            # Marca os ataques como processados
            for ataque in dados:
                flow_id = ataque[0]  # flow_id é o primeiro campo
                self.marcar_ataque_processado(flow_id)
            
            return ips

        except requests.exceptions.ConnectionError:
            logging.error(f"Erro de conexão com a API: {self.api_url}")
            return None
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
        """Loop principal do watchdog"""
        logging.info("Iniciando serviço de monitoramento...")
        
        while True:
            try:
                current_ips = self.get_ips_from_api()
                
                if current_ips is not None and current_ips != self.last_ips:
                    if current_ips:  # Só loga se houver IPs
                        logging.info(f"Detectada mudança na lista de IPs")
                        logging.info(f"IPs anteriores: {self.last_ips}")
                        logging.info(f"Novos IPs: {current_ips}")
                        
                        self.execute_ansible_playbook()
                        self.last_ips = current_ips
                
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logging.info("Serviço interrompido pelo usuário")
                break
            except Exception as e:
                logging.error(f"Erro no loop principal: {str(e)}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    try:
        # Verificar se todas as variáveis de ambiente necessárias estão definidas
        required_vars = ['API_URL', 'API_USERNAME', 'API_PASSWORD', 'CHECK_INTERVAL']
        missing_vars = [var for var in required_vars if var not in os.environ]
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        
        watchdog = AnsibleWatchdog()
        watchdog.run()
    except Exception as e:
        logging.error(f"Erro ao iniciar o watchdog: {str(e)}")