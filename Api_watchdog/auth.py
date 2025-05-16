#!/usr/bin/env python3
import requests
import time
import logging
from datetime import datetime, timedelta
from .config import Config

class APIAuthentication:
    def __init__(self):
        self.config = Config()
        self.access_token = None
        self.token_expiration = None
        self.logger = logging.getLogger(__name__)

    def get_token(self):
        """Obtém token de autenticação com tratamento robusto de erros"""
        try:
            if (self.access_token and self.token_expiration and 
                datetime.now() < self.token_expiration - timedelta(minutes=self.config.TOKEN_REFRESH_MARGIN)):
                return True
                
            response = requests.post(
                f"{self.config.API_URL}/token",
                data={
                    "username": self.config.API_USERNAME,
                    "password": self.config.API_PASSWORD,
                    "grant_type": "password"
                },
                verify=self.config.VERIFY_SSL,
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiration = datetime.now() + timedelta(minutes=self.config.TOKEN_EXPIRATION)
            self.logger.info("Token obtido com sucesso")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter token: {str(e)}")
            self.access_token = None
            self.token_expiration = None
            return False

    def make_authenticated_request(self, method, endpoint, **kwargs):
        """Faz requisições autenticadas com tratamento de token expirado"""
        for attempt in range(self.config.MAX_RETRY_ATTEMPTS):
            if not self.get_token():
                self.logger.error("Falha ao obter token de autenticação")
                return None
                
            headers = kwargs.get('headers', {})
            headers.update({"Authorization": f"Bearer {self.access_token}"})
            kwargs['headers'] = headers
            
            try:
                response = requests.request(
                    method,
                    f"{self.config.API_URL}{endpoint}",
                    verify=self.config.VERIFY_SSL,
                    **kwargs
                )
                
                if response.status_code == 401 and attempt == 0:
                    self.logger.warning("Token expirado, tentando renovar...")
                    self.access_token = None
                    continue
                elif response.status_code == 403:
                    self.logger.error("Acesso negado. Verifique as permissões.")
                    return None
                elif response.status_code >= 500:
                    self.logger.error(f"Erro do servidor: {response.status_code}")
                    time.sleep(self.config.ANSIBLE_RETRY_DELAY)
                    continue
                    
                return response
                
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout na requisição (tentativa {attempt + 1})")
            except requests.exceptions.ConnectionError:
                self.logger.error(f"Erro de conexão (tentativa {attempt + 1})")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erro na requisição (tentativa {attempt + 1}): {str(e)}")
            
            time.sleep(self.config.ANSIBLE_RETRY_DELAY)
                
        return None 