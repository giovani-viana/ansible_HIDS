#!/usr/bin/env python3
import time
import subprocess
import logging
from datetime import datetime
from .auth import APIAuthentication
from .config import Config
import os
import sys

class AnsibleWatchdog(APIAuthentication):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.setup_logging()
        self.logger.info("Iniciando validação de ambiente...")
        self._validate_environment()
        self.logger.info("Ambiente validado com sucesso")

    def setup_logging(self):
        """Configura o sistema de logging"""
        # Configurar o formato do log com cores
        class ColoredFormatter(logging.Formatter):
            """Formatter customizado com cores"""
            grey = "\x1b[38;21m"
            blue = "\x1b[38;5;39m"
            yellow = "\x1b[38;5;226m"
            red = "\x1b[38;5;196m"
            bold_red = "\x1b[31;1m"
            reset = "\x1b[0m"

            def __init__(self, fmt):
                super().__init__()
                self.fmt = fmt
                self.FORMATS = {
                    logging.DEBUG: self.grey + self.fmt + self.reset,
                    logging.INFO: self.blue + self.fmt + self.reset,
                    logging.WARNING: self.yellow + self.fmt + self.reset,
                    logging.ERROR: self.red + self.fmt + self.reset,
                    logging.CRITICAL: self.bold_red + self.fmt + self.reset
                }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt)
                return formatter.format(record)

        # Formato detalhado do log
        log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        
        # Configurar handler para arquivo
        file_handler = logging.FileHandler(self.config.LOG_FILE)
        file_handler.setFormatter(logging.Formatter(log_format))

        # Configurar handler para console com cores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(log_format))

        # Configurar o logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.LOG_LEVEL)
        
        # Remover handlers existentes para evitar duplicação
        self.logger.handlers = []
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

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
            self.logger.info("Nenhum novo ataque detectado")
            return []

        ips = []
        for ataque in ataques:
            if len(ataque) > 1:
                src_ip = ataque[1]
                if src_ip != "0.0.0.0":
                    ips.append((src_ip, ataque[0]))  # Inclui flow_id

        self.logger.info(f"Encontrados {len(ips)} IPs de ataques")
        return ips

    def execute_ansible_playbook(self, flow_id):
        """Executa playbook ansible com melhor tratamento de erros"""
        try:
            self.logger.info("Executando playbook Ansible...")
            process = subprocess.run(
                [
                    "ansible-playbook",
                    self.config.ANSIBLE_PLAYBOOK_PATH,
                    "-i", self.config.ANSIBLE_INVENTORY_PATH,
                    "-vvv"  # Aumentar verbosidade do Ansible
                ],
                capture_output=True,
                text=True,
                timeout=self.config.ANSIBLE_TIMEOUT
            )

            if process.stdout:
                self.logger.info("Saída do Ansible:\n" + process.stdout)
            if process.stderr:
                self.logger.error("Erros do Ansible:\n" + process.stderr)

            return process.returncode == 0

        except subprocess.TimeoutExpired:
            self.logger.error("Playbook Ansible excedeu o tempo limite")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao executar playbook: {str(e)}")
            return False

    def mark_attack_as_resolved(self, flow_id):
        """Marca ataque como processado"""
        response = self.make_authenticated_request(
            'PUT',
            f"/dados/ataques/processar/{flow_id}"
        )
        
        if response and response.status_code == 200:
            self.logger.info(f"Ataque {flow_id} marcado como processado com sucesso!")
            return True
            
        self.logger.error(f"Falha ao marcar ataque {flow_id} como processado")
        return False

    def process_attack(self, ip, flow_id):
        """Processa um ataque individual"""
        self.logger.info(f"Processando IP: {ip} com flow_id: {flow_id}")
        
        if not self.execute_ansible_playbook(flow_id):
            self.logger.error("Falha ao aplicar mitigação")
            return False
            
        self.logger.info("Mitigação aplicada com sucesso")
        
        if self.mark_attack_as_resolved(flow_id):
            return True
            
        self.logger.warning("Mitigação aplicada mas falha ao marcar como resolvido")
        return False

    def run(self):
        """Loop principal do serviço"""
        self.logger.info("Iniciando serviço de monitoramento...")

        while True:
            try:
                ips = self.get_ips_from_api()

                if ips:
                    self.logger.info(f"Novos IPs detectados: {ips}")
                    ip_to_flowids = {}
                    for ip, flow_id in ips:
                        if ip not in ip_to_flowids:
                            ip_to_flowids[ip] = []
                        ip_to_flowids[ip].append(flow_id)

                    for ip, flow_ids in ip_to_flowids.items():
                        self.logger.info(f"Processando IP: {ip} com flow_ids: {flow_ids}")
                        if self.execute_ansible_playbook(flow_ids[0]):
                            self.logger.info(f"Mitigação aplicada com sucesso para o IP {ip}")
                            for flow_id in flow_ids:
                                self.mark_attack_as_resolved(flow_id)
                        else:
                            self.logger.error(f"Falha ao aplicar mitigação para o IP {ip}")

                time.sleep(self.config.CHECK_INTERVAL)

            except Exception as e:
                self.logger.error(f"Erro crítico no loop principal: {str(e)}")
                time.sleep(self.config.CHECK_INTERVAL * 2)

    def _validate_environment(self):
        """Validação completa do ambiente"""
        required_files = [
            self.config.ANSIBLE_INVENTORY_PATH,
            self.config.ANSIBLE_PLAYBOOK_PATH
        ]
        required_scripts = [
            'block_https.sh',
            'restore_https.sh',
            'reset_iptables.sh'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"Arquivo necessário não encontrado: {file}")
            
        for script in required_scripts:
            script_path = os.path.join(self.config.BASE_DIR, 'scripts', script)
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script necessário não encontrado: {script}")
            if not os.access(script_path, os.X_OK):
                raise PermissionError(f"Script não tem permissão de execução: {script}")

if __name__ == "__main__":
    watchdog = AnsibleWatchdog()
    watchdog.run()