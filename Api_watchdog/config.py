import os
from datetime import timedelta

class Config:
    # Configurações da API
    API_URL = "http://164.72.15.30:5050"
    API_USERNAME = "admin"
    API_PASSWORD = "admin"
    VERIFY_SSL = False
    
    # Configurações de arquivos
    STATE_FILE = "state/state.json"
    LOG_FILE = "logs/watchdog.log"
    ANSIBLE_VARS_FILE = "state/ansible_vars.json"
    
    # Configurações de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Configurações de intervalo
    CHECK_INTERVAL = 60  # segundos
    TOKEN_REFRESH_MARGIN = 300  # 5 minutos
    MAX_RETRY_INTERVAL = 300  # 5 minutos
    
    # Security
    SCRIPT_CHECKSUMS_FILE = "data/script_checksums.json"