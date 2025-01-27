#!/bin/bash

# Verifica se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Configurando limite de tráfego HTTP e HTTPS usando iptables..."

# Limpa as regras existentes no iptables para evitar conflitos
sudo iptables -F OUTPUT
sudo iptables -X OUTPUT
sudo iptables -Z OUTPUT

# Definir o limite de tráfego HTTP e HTTPS
LIMIT="10/s"
BURST="20"

# Limitar tráfego HTTP (porta 80) de saída
sudo iptables -A OUTPUT -p tcp --dport 80 -m limit --limit $LIMIT --limit-burst $BURST -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 80 -j REJECT

# Limitaa o tráfego HTTPS de saída
sudo iptables -A OUTPUT -p tcp --dport 443 -m limit --limit $LIMIT --limit-burst $BURST -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 443 -j REJECT

# Permite todo o restante do tráfego de saída
sudo iptables -A OUTPUT -j ACCEPT

echo "Tráfego HTTP e HTTPS configurado com limite de $LIMIT (rajada máxima: $BURST). Todo o restante do tráfego está permitido!"
