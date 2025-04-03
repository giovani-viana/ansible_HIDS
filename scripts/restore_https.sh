#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Restaurando o tráfego HTTP e HTTPS..."

# Limpar as regras de saída (OUTPUT) do iptables
sudo iptables -F OUTPUT
sudo iptables -X OUTPUT
sudo iptables -Z OUTPUT

# Configurar a política padrão para permitir todo o tráfego de saída
sudo iptables -P OUTPUT ACCEPT

echo "Tráfego HTTP e HTTPS restaurado com sucesso! Todo o tráfego de saída agora está permitido."
