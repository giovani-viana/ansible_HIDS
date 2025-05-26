#!/usr/bin/env python3
import json
import sys
import os

# Adicionar o diretório pai ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Api_watchdog.auth import APIAuthentication
from Api_watchdog.config import Config

class DynamicInventory(APIAuthentication):
    def __init__(self):
        super().__init__()
        self.config = Config()

    def get_ips_from_api(self):
        """Obtém os IPs de ataques da API"""
        response = self.make_authenticated_request(
            'GET',
            '/dados/ataques/novos',
            timeout=30
        )
        
        if not response or response.status_code != 200:
            return []

        ataques = response.json().get("dados", [])
        
        if not ataques:
            return []

        ips = []
        for ataque in ataques:
            if len(ataque) > 1:
                src_ip = ataque[1]
                if src_ip != "0.0.0.0":
                    ips.append(src_ip)
        
        return ips

    def generate_inventory(self):
        """Gera o inventário dinâmico para o Ansible"""
        hosts = self.get_ips_from_api()
        
        inventory = {
            "Mirai_Bots": {
                "hosts": [f"{self.config.SSH_USER}@{ip}" for ip in hosts]
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