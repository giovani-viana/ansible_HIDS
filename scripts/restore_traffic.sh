#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Revertendo o bloqueio de tráfego de internet..."

if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
  echo "Revertendo configurações do ufw..."
  
  # Permitir todo o tráfego de saída
  sudo ufw default allow outgoing
  
  echo "Configurações do ufw revertidas com sucesso."

else
  echo "Revertendo configurações do iptables..."

  # Limpar todas as regras de saída e permitir o tráfego
  sudo iptables -F OUTPUT
  sudo iptables -X OUTPUT
  sudo iptables -Z OUTPUT
  sudo iptables -P OUTPUT ACCEPT

  echo "Configurações do iptables revertidas com sucesso."
fi

echo "Tráfego de internet restaurado com sucesso!"
