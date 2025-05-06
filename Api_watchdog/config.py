import os
from datetime import timedelta

class Config:
    # Diretórios
    LOG_DIR = "/app/logs"
    LOG_FILE = f"{LOG_DIR}/watchdog.log"
    STATE_FILE = "/app/state/watchdog_state.json"
    
    # Configurações da API
    API_URL = os.getenv('API_URL', 'http://164.72.15.30:5050')
    API_USERNAME = os.getenv('API_USERNAME', 'hids')
    API_PASSWORD = os.getenv('API_PASSWORD', 'hids')
    
    # Configurações de verificação
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '15'))
    VERIFY_SSL = False
    
    # Configurações de token
    TOKEN_REFRESH_MARGIN = 5  # minutos
    
    # Configurações de retry
    MAX_RETRY_INTERVAL = 300  # 5 minutos
    
    # Configurações de arquivos
    ANSIBLE_VARS_FILE = "state/ansible_vars.json"
    
    # Configurações de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security
    SCRIPT_CHECKSUMS_FILE = "data/script_checksums.json"