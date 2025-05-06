#!/usr/bin/env python3
import json
import sys
import os
import requests
from datetime import datetime, timedelta

class DynamicInventory:
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'http://164.72.15.30:5050')
        self.api_username = os.getenv('API_USERNAME', 'hids')
        self.api_password = os.getenv('API_PASSWORD', 'hids')
        self.access_token = None
        self.token_expiration = None

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
            return True
        except Exception as e:
            print(f"Erro ao obter token: {str(e)}", file=sys.stderr)
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
                return []

            ips = []
            for ataque in ataques:
                if len(ataque) > 1:
                    src_ip = ataque[1]
                    if self.validate_ip(src_ip):
                        ips.append(f"pi@{src_ip}")
            
            return ips

        except Exception as e:
            print(f"Erro ao obter IPs: {str(e)}", file=sys.stderr)
            return []

    def validate_ip(self, ip):
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def generate_inventory(self):
        hosts = self.get_ips_from_api()
        
        inventory = {
            "Mirai_Bots": {
                "hosts": hosts,
                "vars": {
                    "ansible_user": "pi",
                    "ansible_ssh_common_args": "-o StrictHostKeyChecking=no"
                }
            },
            "_meta": {
                "hostvars": {}
            }
        }
        
        return inventory

def main():
    inventory = DynamicInventory()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        print(json.dumps(inventory.generate_inventory()))
    elif len(sys.argv) > 2 and sys.argv[1] == '--host':
        print(json.dumps({}))
    else:
        print("Uso: --list ou --host <hostname>", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 