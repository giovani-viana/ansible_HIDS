#!/bin/bash

# Verify permission 
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

# Verificar se o serviço SSH está em execução
if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
  echo "Parando o serviço SSH..."
  
  # Tentar parar o serviço SSH usando systemd (mais moderno e compatível)
  if systemctl is-active --quiet sshd; then
    systemctl stop sshd
    echo "Serviço SSH (sshd) parado com sucesso!"
  elif systemctl is-active --quiet ssh; then
    systemctl stop ssh
    echo "Serviço SSH (ssh) parado com sucesso!"
  else
    # Como fallback, tentar usar o init.d (caso não esteja usando systemd)
    echo "Tentando parar o serviço via init.d..."
    /etc/init.d/ssh stop
    echo "Serviço SSH parado com sucesso (via init.d)!"
  fi
else
  echo "O serviço SSH não está em execução."
fi

# Bloquear a porta 22 no firewall (usando ufw ou iptables)

echo "Bloqueando a porta 22 no firewall..."

# Verificar se o ufw está instalado e habilitado
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
  echo "Usando ufw para bloquear a porta 22..."
  sudo ufw deny 22
  echo "Porta 22 bloqueada com sucesso no ufw."
else
  # Caso não tenha o ufw, usar iptables como alternativa
  echo "Usando iptables para bloquear a porta 22..."
  sudo iptables -A INPUT -p tcp --dport 22 -j REJECT
  echo "Porta 22 bloqueada com sucesso no iptables."
fi
