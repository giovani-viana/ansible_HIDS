#!/usr/bin/env python3
import requests
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import os
import json
import hashlib
from pathlib import Path
from config import Config

class StateManager:
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = self.load_state()
        
    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {"last_ips": [], "last_update": None}
            
    def save_state(self, ips):
        state = {
            "last_ips": list(ips),
            "last_update": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
            
    @property
    def last_ips(self):
        return set(self.state.get("last_ips", []))

class AnsibleWatchdog:
    def __init__(self):
        self.setup_logging()
        self.state_manager = StateManager(Config.STATE_FILE)
        self.access_token = None
        self.token_expiration = None
        self.retry_attempt = 0
        
    def setup_logging(self):
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            handlers=[handler, logging.StreamHandler()]
        )
        
    def get_token(self):
        if (self.access_token and self.token_expiration and 
            datetime.now() < self.token_expiration - Config.TOKEN_REFRESH_MARGIN):
            return True
            
        try:
            response = requests.post(
                f"{Config.API_URL}/token",
                data={
                    "username": Config.API_USERNAME,
                    "password": Config.API_PASSWORD,
                    "grant_type": "password"
                },
                verify=Config.VERIFY_SSL
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiration = datetime.now() + timedelta(minutes=30)
            logging.info("Token de autenticação obtido com sucesso")
            return True
        except requests.RequestException as e:
            logging.error(f"Erro na requisição do token: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Erro ao obter token: {str(e)}")
            return False

    def validate_ip(self, ip):
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def get_ips_from_api(self):
        if not self.access_token and not self.get_token():
            return None, []

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{Config.API_URL}/dados/ataques/novos",
                headers=headers,
                timeout=30,
                verify=Config.VERIFY_SSL
            )
            
            if response.status_code == 401:
                if not self.get_token():
                    return None, []
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    f"{Config.API_URL}/dados/ataques/novos",
                    headers=headers,
                    timeout=30,
                    verify=Config.VERIFY_SSL
                )

            response.raise_for_status()
            ataques = response.json().get("dados", [])
                        
            if not ataques:
                logging.info("Nenhum novo ataque detectado")
                return set(), []

            ips = set()
            flow_ids = []
            for ataque in ataques:
                if len(ataque) > 1:
                    flow_id = ataque[0]
                    src_ip = ataque[1]
                    if self.validate_ip(src_ip):
                        ips.add(f"pi@{src_ip}")
                        flow_ids.append(flow_id)
            
            logging.info(f"Encontrados {len(ips)} IPs únicos de ataques")
            return ips, flow_ids

        except requests.RequestException as e:
            logging.error(f"Erro na requisição da API: {str(e)}")
            return None, []
        except Exception as e:
            logging.error(f"Erro ao obter IPs: {str(e)}")
            return None, []

    def save_ansible_vars(self, ips, flow_ids):
        """Salva as variáveis necessárias para o Ansible em um arquivo JSON"""
        ansible_vars = {
            "target_ips": ",".join(ips),
            "flow_ids": flow_ids,
            "access_token": self.access_token
        }
        
        os.makedirs(os.path.dirname(Config.ANSIBLE_VARS_FILE), exist_ok=True)
        with open(Config.ANSIBLE_VARS_FILE, 'w') as f:
            json.dump(ansible_vars, f)
        logging.info(f"Variáveis do Ansible salvas em {Config.ANSIBLE_VARS_FILE}")

    def run(self):
        logging.info("Iniciando serviço de monitoramento...")
        
        while True:
            try:
                current_ips, flow_ids = self.get_ips_from_api()
                
                if current_ips is not None and current_ips != self.state_manager.last_ips:
                    logging.info(f"Detectada mudança na lista de IPs")
                    logging.info(f"IPs anteriores: {self.state_manager.last_ips}")
                    logging.info(f"Novos IPs: {current_ips}")
                    
                    if current_ips:
                        self.state_manager.save_state(current_ips)
                        self.save_ansible_vars(current_ips, flow_ids)
                        logging.info("Arquivos de configuração atualizados. Execute o playbook Ansible manualmente.")
                
                time.sleep(Config.CHECK_INTERVAL)
                
            except Exception as e:
                logging.error(f"Erro no loop principal: {str(e)}")
                delay = self.exponential_backoff()
                logging.info(f"Aguardando {delay} segundos antes de tentar novamente")
                time.sleep(delay)

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()