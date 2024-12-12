#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

# Reiniciar o serviço SSH (sshd ou ssh)
echo "Reiniciando o serviço SSH..."

if systemctl is-active --quiet sshd; then
  systemctl start sshd
  echo "Serviço SSH (sshd) reiniciado com sucesso!"
elif systemctl is-active --quiet ssh; then
  systemctl start ssh
  echo "Serviço SSH (ssh) reiniciado com sucesso!"
else
  echo "Serviço SSH não encontrado!"
fi

# Desbloquear a porta 22 no firewall
echo "Desbloqueando a porta 22 no firewall..."

# Verificar se o ufw está em uso
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
  echo "Usando ufw para desbloquear a porta 22..."
  sudo ufw allow 22
  echo "Porta 22 desbloqueada com sucesso no ufw."
else
  # Caso o ufw não esteja em uso, usar iptables
  echo "Usando iptables para desbloquear a porta 22..."
  sudo iptables -D INPUT -p tcp --dport 22 -j REJECT
  echo "Porta 22 desbloqueada com sucesso no iptables."
fi

echo "Acesso SSH restaurado!"
