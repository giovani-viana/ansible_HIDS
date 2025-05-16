#!/bin/bash

# Verifica se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

echo "Restaurando configurações do iptables para o padrão..."

# Limpar todas as regras existentes
sudo iptables -F
sudo iptables -X
sudo iptables -Z

# Configurar política padrão para ACCEPT
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

echo "Configurações do iptables restauradas para o padrão."
