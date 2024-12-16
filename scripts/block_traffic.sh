#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Iniciando o bloqueio de tráfego de internet, mas mantendo o SSH ativo..."

# Bloquear tráfego de saída com ufw ou iptables
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
  echo "Usando ufw para bloquear o tráfego..."

  # Bloquear todo o tráfego de saída
  sudo ufw default deny outgoing

  # Permitir tráfego local (localhost)
  sudo ufw allow out on lo

  # Permitir conexões SSH (porta 22)
  sudo ufw allow out 22/tcp

  echo "Bloqueio de tráfego configurado com sucesso usando ufw, com SSH permitido."

else
  echo "Usando iptables para bloquear o tráfego..."

  # Limpar regras existentes
  sudo iptables -F OUTPUT
  sudo iptables -X OUTPUT
  sudo iptables -Z OUTPUT

  # Bloquear todo o tráfego de saída por padrão
  sudo iptables -P OUTPUT DROP

  # Permitir tráfego local (localhost)
  sudo iptables -A OUTPUT -o lo -j ACCEPT

  # Permitir conexões SSH (porta 22)
  sudo iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT

  echo "Bloqueio de tráfego configurado com sucesso usando iptables, com SSH permitido."
fi

echo "Tráfego de internet bloqueado com sucesso, mas conexões SSH estão ativas!"
