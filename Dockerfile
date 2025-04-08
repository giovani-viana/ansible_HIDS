# Base image
FROM ubuntu:20.04

# Configurações básicas
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ansible \
    iptables \
    curl \
    sudo \
    && apt-get clean

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos do projeto
COPY . /app

# Instalar dependências do Python
RUN pip3 install -r ./requirements.txt

# Permitir execução dos scripts
RUN chmod +x scripts/*.sh

# Configurar o Ansible
ENV ANSIBLE_CONFIG=/app/ansible.cfg

# Comando padrão
CMD ["python3", "Api_watchdog/watchdog_service.py"]