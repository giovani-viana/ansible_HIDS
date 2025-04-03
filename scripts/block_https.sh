#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Iniciando o bloqueio de tráfego HTTP e HTTPS usando iptables..."

# Limpar regras existentes para evitar conflitos
sudo iptables -F OUTPUT
sudo iptables -X OUTPUT
sudo iptables -Z OUTPUT

# Bloquear tráfego HTTP (porta 80) de saída
sudo iptables -A OUTPUT -p tcp --dport 80 -j REJECT
sudo iptables -A OUTPUT -p udp --dport 80 -j REJECT

# Bloquear tráfego HTTPS (porta 443) de saída
sudo iptables -A OUTPUT -p tcp --dport 443 -j REJECT
sudo iptables -A OUTPUT -p udp --dport 443 -j REJECT

# Permitir todo o restante do tráfego de saída
sudo iptables -A OUTPUT -j ACCEPT

echo "Tráfego HTTP e HTTPS bloqueado com sucesso. Todo o restante do tráfego está permitido!"
