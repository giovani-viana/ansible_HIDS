import os
from datetime import timedelta

class Config:
    """
    Configurações centralizadas para o sistema de monitoramento Ansible.
    Todas as configurações podem ser sobrescritas por variáveis de ambiente.
    """
    
    # Diretórios
    BASE_DIR = "/app"
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    STATE_DIR = os.path.join(BASE_DIR, "state")
    LOG_FILE = os.path.join(LOG_DIR, "watchdog.log")
    STATE_FILE = os.path.join(STATE_DIR, "watchdog_state.json")
    
    # Configurações da API
    API_URL = os.getenv('API_URL', 'http://164.72.15.30:5050')
    API_USERNAME = os.getenv('API_USERNAME', 'hids')
    API_PASSWORD = os.getenv('API_PASSWORD', 'hids')
    
    # Configurações de verificação
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '15'))
    VERIFY_SSL = os.getenv('VERIFY_SSL', 'false').lower() == 'true'
    
    # Configurações de token
    TOKEN_REFRESH_MARGIN = 5  # minutos
    TOKEN_EXPIRATION = 30  # minutos
    
    # Configurações de retry
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
    MAX_RETRY_INTERVAL = int(os.getenv('MAX_RETRY_INTERVAL', '300'))  # 5 minutos
    
    # Configurações de arquivos
    ANSIBLE_VARS_FILE = os.path.join(STATE_DIR, "ansible_vars.json")
    PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE', '/home/hids/.ssh/ansible_key')
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Ansible
    ANSIBLE_TIMEOUT = int(os.getenv('ANSIBLE_TIMEOUT', '60'))  # Aumentado para 60 segundos
    ANSIBLE_RETRY_COUNT = int(os.getenv('ANSIBLE_RETRY_COUNT', '3'))
    ANSIBLE_RETRY_DELAY = int(os.getenv('ANSIBLE_RETRY_DELAY', '5'))
    ANSIBLE_PLAYBOOK_PATH = os.getenv('ANSIBLE_PLAYBOOK_PATH', '/home/hids/ansible_HIPS/Playbooks')
    ANSIBLE_INVENTORY_PATH = os.getenv('ANSIBLE_INVENTORY_PATH', 'Api_watchdog/dynamic_inventory.py')
    ANSIBLE_REMOTE_USER = os.getenv('ANSIBLE_REMOTE_USER', 'pi')
    
    # SSH
    SSH_USER = os.getenv('SSH_USER', 'pi')
    SSH_STRICT_HOST_KEY_CHECKING = os.getenv('SSH_STRICT_HOST_KEY_CHECKING', 'false').lower() == 'true'
    SSH_USER_KNOWN_HOSTS_FILE = os.getenv('SSH_USER_KNOWN_HOSTS_FILE', '/dev/null')
    SSH_COMMON_ARGS = f"-o StrictHostKeyChecking={'no' if not SSH_STRICT_HOST_KEY_CHECKING else 'yes'} -o UserKnownHostsFile={SSH_USER_KNOWN_HOSTS_FILE}"

    def __init__(self):
        """Valida as configurações ao inicializar"""
        self._validate_configs()

    def _validate_configs(self):
        """Valida as configurações críticas"""
        if not self.API_URL:
            raise ValueError("API_URL não pode estar vazio")
        if not self.API_USERNAME:
            raise ValueError("API_USERNAME não pode estar vazio")
        if not self.API_PASSWORD:
            raise ValueError("API_PASSWORD não pode estar vazio")
        if self.CHECK_INTERVAL < 1:
            raise ValueError("CHECK_INTERVAL deve ser maior que 0")
        if self.MAX_RETRY_ATTEMPTS < 1:
            raise ValueError("MAX_RETRY_ATTEMPTS deve ser maior que 0")
        if self.ANSIBLE_TIMEOUT < 1:
            raise ValueError("ANSIBLE_TIMEOUT deve ser maior que 0")
        self._validate_ssh_config()

    def _validate_ssh_config(self):
        if not os.path.exists(self.PRIVATE_KEY_FILE):
            raise ValueError(f"Chave SSH não encontrada em {self.PRIVATE_KEY_FILE}")
