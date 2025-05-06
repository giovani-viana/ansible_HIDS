#!/usr/bin/env python3
import json
import sys
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config

class DynamicInventory:
    def __init__(self):
        self.setup_logging()
        self.api_url = os.getenv('API_URL', Config.API_URL)
        self.api_username = os.getenv('API_USERNAME', Config.API_USERNAME)
        self.api_password = os.getenv('API_PASSWORD', Config.API_PASSWORD)
        self.access_token = None
        self.token_expiration = None
        self.retry_count = 0

    def setup_logging(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            logging.basicConfig(
                level=Config.LOG_LEVEL,
                format=Config.LOG_FORMAT,
                handlers=[
                    logging.FileHandler(Config.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
        except Exception as e:
            print(f"Erro ao configurar logging: {str(e)}", file=sys.stderr)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                stream=sys.stderr
            )

    def get_token(self) -> bool:
        if (self.access_token and self.token_expiration and 
            datetime.now() < self.token_expiration - timedelta(minutes=Config.TOKEN_REFRESH_MARGIN)):
            return True
            
        try:
            response = requests.post(
                f"{self.api_url}/token",
                data={
                    "username": self.api_username,
                    "password": self.api_password,
                    "grant_type": "password"
                },
                verify=Config.VERIFY_SSL,
                timeout=Config.ANSIBLE_TIMEOUT
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiration = datetime.now() + timedelta(minutes=Config.TOKEN_EXPIRATION)
            logging.info("Token obtido com sucesso")
            return True
        except requests.RequestException as e:
            logging.error(f"Erro na requisição do token: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Erro ao obter token: {str(e)}")
            return False

    def get_ips_from_api(self) -> List[str]:
        if not self.access_token and not self.get_token():
            return []

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_url}/dados/ataques/novos",
                headers=headers,
                timeout=Config.ANSIBLE_TIMEOUT,
                verify=Config.VERIFY_SSL
            )
            
            if response.status_code == 401:
                if not self.get_token():
                    return []
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    f"{self.api_url}/dados/ataques/novos",
                    headers=headers,
                    timeout=Config.ANSIBLE_TIMEOUT,
                    verify=Config.VERIFY_SSL
                )

            response.raise_for_status()
            ataques = response.json().get("dados", [])
            
            if not ataques:
                logging.info("Nenhum novo ataque detectado")
                return []

            ips = []
            for ataque in ataques:
                if len(ataque) > 1:
                    src_ip = ataque[1]
                    if self.validate_ip(src_ip) and src_ip != "0.0.0.0":
                        ips.append(src_ip)
                        logging.debug(f"IP válido encontrado: {src_ip}")
                    else:
                        logging.warning(f"IP inválido detectado e ignorado: {src_ip}")
            
            logging.info(f"Total de {len(ips)} IPs válidos encontrados")
            return ips

        except requests.RequestException as e:
            logging.error(f"Erro na requisição da API: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Erro ao obter IPs: {str(e)}")
            return []

    def validate_ip(self, ip: str) -> bool:
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def generate_inventory(self) -> Dict:
        hosts = self.get_ips_from_api()
        
        inventory = {
            "Mirai_Bots": {
                "hosts": [],
                "vars": {
                    "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
                    "ansible_ssh_private_key_file": Config.PRIVATE_KEY_FILE,
                    "ansible_become": True,
                    "ansible_become_method": "sudo",
                    "ansible_become_user": "root"
                }
            }
        }

        for ip in hosts:
            hostname = f"pi@{ip}"
            inventory["Mirai_Bots"]["hosts"].append(hostname)
            logging.debug(f"Host adicionado ao inventário: {hostname}")
        
        return inventory

def main():
    try:
        inventory = DynamicInventory()
        
        if len(sys.argv) > 1 and sys.argv[1] == '--list':
            print(json.dumps(inventory.generate_inventory()))
        elif len(sys.argv) > 2 and sys.argv[1] == '--host':
            print(json.dumps({}))
        else:
            logging.error("Uso: --list ou --host <hostname>")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Erro fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()