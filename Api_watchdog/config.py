import os
from datetime import timedelta

class Config:
    # API Configuration
    API_URL = os.getenv("API_URL", "http://164.72.15.30:5050")
    API_USERNAME = os.getenv("API_USERNAME", "hids")
    API_PASSWORD = os.getenv("API_PASSWORD", "hids")
    
    # Intervals
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 minutos
    TOKEN_REFRESH_MARGIN = timedelta(minutes=5)
    MAX_RETRY_INTERVAL = 300  # 5 minutos
    
    # Logging
    LOG_FILE = "logs/watchdog.log"
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # State
    STATE_FILE = "data/watchdog_state.json"
    
    # Security
    VERIFY_SSL = True
    SCRIPT_CHECKSUMS_FILE = "data/script_checksums.json"