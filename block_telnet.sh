#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

# Verificar se o serviço inetd está em execução
if systemctl is-active --quiet inetd || systemctl is-active --quiet xinetd; then
  echo "Parando o serviço inetd..."
  
  # Tentar parar o serviço usando systemd (preferencialmente)
  if systemctl is-active --quiet inetd; then
    systemctl stop inetd
    echo "Serviço inetd parado com sucesso!"
  elif systemctl is-active --quiet xinetd; then
    systemctl stop xinetd
    echo "Serviço xinetd parado com sucesso!"
  else
    # Como fallback, tentar usar o init.d (caso não esteja usando systemd)
    echo "Tentando parar o serviço via init.d..."
    /etc/init.d/inetd stop
    echo "Serviço inetd parado com sucesso (via init.d)!"
  fi
else
  echo "O serviço inetd não está em execução."
fi
