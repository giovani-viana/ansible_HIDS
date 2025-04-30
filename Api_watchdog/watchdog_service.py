#!/usr/bin/env python3
import requests
import time
import subprocess
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

class SecurityManager:
    def __init__(self, checksums_file):
        self.checksums_file = checksums_file
        self.load_checksums()
        
    def load_checksums(self):
        try:
            with open(self.checksums_file, 'r') as f:
                self.checksums = json.load(f)
        except:
            self.checksums = {}
            
    def verify_script(self, script_path):
        if not os.path.exists(script_path):
            return False
            
        with open(script_path, 'rb') as f:
            content = f.read()
            current_hash = hashlib.sha256(content).hexdigest()
            
        return current_hash == self.checksums.get(script_path)
        
    def update_checksum(self, script_path):
        with open(script_path, 'rb') as f:
            content = f.read()
            self.checksums[script_path] = hashlib.sha256(content).hexdigest()
            
        os.makedirs(os.path.dirname(self.checksums_file), exist_ok=True)
        with open(self.checksums_file, 'w') as f:
            json.dump(self.checksums, f)

class AnsibleWatchdog:
    def __init__(self):
        self.setup_logging()
        self.state_manager = StateManager(Config.STATE_FILE)
        self.security_manager = SecurityManager(Config.SCRIPT_CHECKSUMS_FILE)
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
            # Assumindo que o token expira em 30 minutos
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
                        ips.add(src_ip)
                        flow_ids.append(flow_id)
                    else:
                        logging.warning(f"IP inválido ignorado: {src_ip}")
            
            logging.info(f"Encontrados {len(ips)} IPs únicos de ataques")
            return ips, flow_ids

        except requests.RequestException as e:
            logging.error(f"Erro na requisição da API: {str(e)}")
            return None, []
        except Exception as e:
            logging.error(f"Erro ao obter IPs: {str(e)}")
            return None, []

    def verify_scripts(self):
        scripts = ['./scripts/block_https.sh', './scripts/limit_https.sh']
        for script in scripts:
            if not self.security_manager.verify_script(script):
                logging.error(f"Verificação de integridade falhou para {script}")
                return False
        return True

    def execute_ansible_playbook(self, flow_ids):
        if not self.verify_scripts():
            logging.error("Verificação de scripts falhou")
            return False

        try:
            logging.info("Executando playbook Ansible...")
            ips_str = ','.join(self.state_manager.last_ips)
            flow_ids_str = ','.join(map(str, flow_ids))
            
            result = subprocess.run(
                [
                    "ansible-playbook",
                    "rules_playbook.yml",
                    "-e", f"target_ips={ips_str}",
                    "-e", f"flow_ids={flow_ids_str}",
                    "-e", f"access_token={self.access_token}",
                    "-vvv"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logging.info("Playbook executado com sucesso")
            self.retry_attempt = 0
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Erro na execução do playbook: {e.stderr}")
            return False
        except Exception as e:
            logging.error(f"Erro ao executar playbook: {str(e)}")
            return False

    def exponential_backoff(self):
        delay = min(Config.MAX_RETRY_INTERVAL, 
                   Config.CHECK_INTERVAL * (2 ** self.retry_attempt))
        self.retry_attempt += 1
        return delay

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
                        if self.execute_ansible_playbook(flow_ids):
                            for flow_id in flow_ids:
                                self.marcar_ataque_processado(flow_id)
                
                time.sleep(Config.CHECK_INTERVAL)
                
            except Exception as e:
                logging.error(f"Erro no loop principal: {str(e)}")
                delay = self.exponential_backoff()
                logging.info(f"Aguardando {delay} segundos antes de tentar novamente")
                time.sleep(delay)

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()