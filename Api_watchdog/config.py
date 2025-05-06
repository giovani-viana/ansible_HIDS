import os
from datetime import timedelta

class Config:
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
    VERIFY_SSL = False
    
    # Configurações de token
    TOKEN_REFRESH_MARGIN = 5  # minutos
    TOKEN_EXPIRATION = 30  # minutos
    REFRESH_TOKEN_EXPIRATION = 60 * 24 * 7  # 7 dias
    
    # Configurações de retry
    MAX_RETRY_INTERVAL = 300  # 5 minutos
    MAX_RETRY_ATTEMPTS = 5
    
    # Configurações de arquivos
    ANSIBLE_VARS_FILE = os.path.join(STATE_DIR, "ansible_vars.json")
    PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE', '/home/hids/.ssh/id_rsa')
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security
    SCRIPT_CHECKSUMS_FILE = os.path.join(BASE_DIR, "data/script_checksums.json")
    
    # Ansible
    ANSIBLE_TIMEOUT = 30
    ANSIBLE_RETRY_COUNT = 3
    ANSIBLE_RETRY_DELAY = 5
    
    # Status possíveis para IPs
    IP_STATUS = {
        'PENDING': 'pending',
        'COMPLETED': 'completed',
        'PARTIAL': 'partial',
        'FAILED': 'failed',
        'ERROR': 'error'
    }
    
    # SSH
    SSH_STRICT_HOST_KEY_CHECKING = False
    SSH_USER_KNOWN_HOSTS_FILE = "/dev/null"
    SSH_COMMON_ARGS = f"-o StrictHostKeyChecking={'no' if not SSH_STRICT_HOST_KEY_CHECKING else 'yes'} -o UserKnownHostsFile={SSH_USER_KNOWN_HOSTS_FILE}"