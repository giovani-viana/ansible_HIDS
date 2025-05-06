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
import sys
import sqlite3
from typing import Optional, Tuple, Set, List

class TokenManager:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiration: Optional[datetime] = None
        self.token_db_path = os.path.join(Config.STATE_DIR, 'tokens.db')
        self._init_db()
        
    def _init_db(self):
        os.makedirs(os.path.dirname(self.token_db_path), exist_ok=True)
        with sqlite3.connect(self.token_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    access_token TEXT,
                    refresh_token TEXT,
                    expiration TIMESTAMP
                )
            ''')
            self._load_tokens()
    
    def _load_tokens(self):
        try:
            with sqlite3.connect(self.token_db_path) as conn:
                cursor = conn.execute('SELECT access_token, refresh_token, expiration FROM tokens LIMIT 1')
                row = cursor.fetchone()
                if row:
                    self.access_token, self.refresh_token, expiration = row
                    self.token_expiration = datetime.fromisoformat(expiration)
        except Exception as e:
            logging.error(f"Erro ao carregar tokens: {e}")
    
    def _save_tokens(self):
        try:
            with sqlite3.connect(self.token_db_path) as conn:
                conn.execute('DELETE FROM tokens')
                conn.execute(
                    'INSERT INTO tokens (access_token, refresh_token, expiration) VALUES (?, ?, ?)',
                    (self.access_token, self.refresh_token, self.token_expiration.isoformat())
                )
        except Exception as e:
            logging.error(f"Erro ao salvar tokens: {e}")
    
    def get_valid_token(self) -> Optional[str]:
        if (self.access_token and self.token_expiration and 
            datetime.now() < self.token_expiration - timedelta(minutes=Config.TOKEN_REFRESH_MARGIN)):
            return self.access_token
            
        if self.refresh_token:
            if self._refresh_token():
                return self.access_token
                
        if self._get_new_token():
            return self.access_token
            
        return None
    
    def _get_new_token(self) -> bool:
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
            self.refresh_token = token_data.get("refresh_token")
            self.token_expiration = datetime.now() + timedelta(minutes=30)
            self._save_tokens()
            logging.info("Novo token obtido com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao obter novo token: {e}")
            return False
    
    def _refresh_token(self) -> bool:
        try:
            response = requests.post(
                f"{Config.API_URL}/token/refresh",
                data={
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                },
                verify=Config.VERIFY_SSL
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            self.token_expiration = datetime.now() + timedelta(minutes=30)
            self._save_tokens()
            logging.info("Token atualizado com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao atualizar token: {e}")
            return False

class StateManager:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state_db_path = os.path.join(Config.STATE_DIR, 'state.db')
        self._init_db()
        
    def _init_db(self):
        os.makedirs(os.path.dirname(self.state_db_path), exist_ok=True)
        with sqlite3.connect(self.state_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    ip TEXT PRIMARY KEY,
                    last_update TIMESTAMP,
                    status TEXT,
                    flow_id TEXT
                )
            ''')
    
    def save_state(self, ips: Set[str], flow_ids: List[str]):
        try:
            with sqlite3.connect(self.state_db_path) as conn:
                for ip, flow_id in zip(ips, flow_ids):
                    conn.execute('''
                        INSERT OR REPLACE INTO state (ip, last_update, status, flow_id)
                        VALUES (?, ?, ?, ?)
                    ''', (ip, datetime.now().isoformat(), 'pending', flow_id))
        except Exception as e:
            logging.error(f"Erro ao salvar estado: {e}")
    
    def get_pending_ips(self) -> Set[str]:
        try:
            with sqlite3.connect(self.state_db_path) as conn:
                cursor = conn.execute('SELECT ip FROM state WHERE status = ?', ('pending',))
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logging.error(f"Erro ao obter IPs pendentes: {e}")
            return set()
    
    def update_status(self, ip: str, status: str):
        try:
            with sqlite3.connect(self.state_db_path) as conn:
                conn.execute('UPDATE state SET status = ? WHERE ip = ?', (status, ip))
        except Exception as e:
            logging.error(f"Erro ao atualizar status: {e}")

class AnsibleWatchdog:
    def __init__(self):
        self.setup_logging()
        self.state_manager = StateManager(Config.STATE_FILE)
        self.token_manager = TokenManager()
        self.retry_attempt = 0
        
    def setup_logging(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            
            formatter = logging.Formatter(Config.LOG_FORMAT)
            
            file_handler = RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=Config.LOG_MAX_SIZE,
                backupCount=Config.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            logging.info("Logging configurado com sucesso")
            
        except Exception as e:
            print(f"Erro ao configurar logging: {str(e)}")
            logging.basicConfig(
                level=logging.INFO,
                format=Config.LOG_FORMAT,
                stream=sys.stdout
            )
            logging.error(f"Erro ao configurar logging: {str(e)}")

    def validate_ip(self, ip: str) -> bool:
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def get_ips_from_api(self) -> Tuple[Optional[Set[str]], List[str]]:
        token = self.token_manager.get_valid_token()
        if not token:
            return None, []

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{Config.API_URL}/dados/ataques/novos",
                headers=headers,
                timeout=30,
                verify=Config.VERIFY_SSL
            )
            
            if response.status_code == 401:
                if not self.token_manager._get_new_token():
                    return None, []
                headers = {"Authorization": f"Bearer {self.token_manager.access_token}"}
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
                    if self.validate_ip(src_ip) and src_ip != "0.0.0.0":
                        ips.add(f"pi@{src_ip}")
                        flow_ids.append(flow_id)
                    else:
                        logging.warning(f"IP inválido detectado e ignorado: {src_ip}")
            
            logging.info(f"Encontrados {len(ips)} IPs únicos de ataques")
            return ips, flow_ids

        except requests.RequestException as e:
            logging.error(f"Erro na requisição da API: {str(e)}")
            return None, []
        except Exception as e:
            logging.error(f"Erro ao obter IPs: {str(e)}")
            return None, []

    def execute_ansible_playbook(self, ips: Set[str], flow_ids: List[str]) -> bool:
        try:
            logging.info("Executando playbook Ansible...")
            flow_ids_str = ','.join(map(str, flow_ids))
            
            process = subprocess.Popen(
                [
                    "ansible-playbook",
                    "rules_playbook.yml",
                    "-i", "Api_watchdog/dynamic_inventory.py",
                    "-e", f"flow_ids={flow_ids_str}",
                    "-e", f"access_token={self.token_manager.access_token}",
                    "-vvvv"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            for line in process.stdout:
                if "extra_vars" not in line:
                    print(line, end='')
                    logging.info(line.strip())

            process.wait()
            
            if process.returncode == 0:
                logging.info("Playbook executado com sucesso")
                self.retry_attempt = 0
                for ip in ips:
                    self.state_manager.update_status(ip, 'completed')
                return True
            elif process.returncode == 4:
                logging.warning("Alguns hosts estão inacessíveis, mas o playbook continuou para os hosts acessíveis")
                self.retry_attempt = 0
                for ip in ips:
                    self.state_manager.update_status(ip, 'partial')
                return True
            else:
                logging.error(f"Playbook falhou com código de retorno {process.returncode}")
                for ip in ips:
                    self.state_manager.update_status(ip, 'failed')
                return False
            
        except Exception as e:
            logging.error(f"Erro inesperado: {str(e)}")
            for ip in ips:
                self.state_manager.update_status(ip, 'error')
            return False

    def exponential_backoff(self) -> int:
        delay = min(Config.MAX_RETRY_INTERVAL, 
                   Config.CHECK_INTERVAL * (2 ** self.retry_attempt))
        self.retry_attempt += 1
        return delay

    def run(self):
        logging.info("Iniciando serviço de monitoramento...")
        
        while True:
            try:
                current_ips, flow_ids = self.get_ips_from_api()
                
                if current_ips is not None:
                    logging.info(f"Detectada lista de IPs")
                    logging.info(f"Novos IPs: {current_ips}")
                    
                    if current_ips:
                        self.state_manager.save_state(current_ips, flow_ids)
                        if self.execute_ansible_playbook(current_ips, flow_ids):
                            logging.info("Mitigação aplicada com sucesso")
                        else:
                            logging.error("Falha ao aplicar mitigação")
            
                time.sleep(Config.CHECK_INTERVAL)
        
            except Exception as e:
                logging.error(f"Erro no loop principal: {str(e)}")
                delay = self.exponential_backoff()
                logging.info(f"Aguardando {delay} segundos antes de tentar novamente")
                time.sleep(delay)

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()