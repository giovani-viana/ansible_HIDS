#!/usr/bin/env python3
import json
import subprocess
import logging
from config import Config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_ansible_vars():
    try:
        with open(Config.ANSIBLE_VARS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Arquivo de variáveis do Ansible não encontrado: {Config.ANSIBLE_VARS_FILE}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar arquivo de variáveis do Ansible: {Config.ANSIBLE_VARS_FILE}")
        return None

def run_ansible_playbook(vars_dict):
    try:
        cmd = [
            "ansible-playbook",
            "rules_playbook.yml",
            "-e", f"target_ips={vars_dict['target_ips']}",
            "-e", f"flow_ids={vars_dict['flow_ids']}",
            "-e", f"access_token={vars_dict['access_token']}",
            "-vvv"
        ]
        
        logging.info("Executando playbook Ansible...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logging.info("Playbook executado com sucesso")
        logging.info(f"STDOUT do playbook:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"STDERR do playbook:\n{result.stderr}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro na execução do playbook: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
        return False

def main():
    setup_logging()
    logging.info("Iniciando execução manual do Ansible...")
    
    vars_dict = load_ansible_vars()
    if not vars_dict:
        return
    
    if run_ansible_playbook(vars_dict):
        logging.info("Execução do Ansible concluída com sucesso")
    else:
        logging.error("Falha na execução do Ansible")

if __name__ == "__main__":
    main() 