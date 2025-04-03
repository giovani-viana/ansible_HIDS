#!/bin/bash

# Verificar se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root!"
  exit 1
fi

# Reiniciar o serviço inetd ou xinetd
echo "Reiniciando o serviço inetd ou xinetd..."

if systemctl is-active --quiet inetd; then
  systemctl start inetd
  echo "Serviço inetd reiniciado com sucesso!"
elif systemctl is-active --quiet xinetd; then
  systemctl start xinetd
  echo "Serviço xinetd reiniciado com sucesso!"
else
  # Como fallback, tentar usar init.d (caso não esteja usando systemd)
  echo "Tentando reiniciar o serviço via init.d..."
  if /etc/init.d/inetd start; then
    echo "Serviço inetd reiniciado com sucesso (via init.d)!"
  elif /etc/init.d/xinetd start; then
    echo "Serviço xinetd reiniciado com sucesso (via init.d)!"
  else
    echo "Não foi possível reiniciar os serviços inetd ou xinetd!"
  fi
fi

echo "Restauração do serviço inetd/xinetd concluída!"
