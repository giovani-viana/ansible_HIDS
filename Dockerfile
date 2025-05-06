FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    openssh-client \
    ansible \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios necessários
RUN mkdir -p /app/state /app/logs /app/scripts && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/state

# Copiar arquivos da aplicação
COPY Api_watchdog /app/Api_watchdog
COPY rules_playbook.yml /app/
COPY run_ansible.py /app/
COPY scripts /app/scripts/

# Configurar diretório de trabalho
WORKDIR /app

# Instalar dependências Python
RUN pip install requests

# Tornar o script de inventário dinâmico executável
RUN chmod +x /app/Api_watchdog/dynamic_inventory.py

# Criar usuário não-root e configurar permissões
RUN useradd -m -s /bin/bash hids && \
    chown -R hids:hids /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/state && \
    touch /app/logs/watchdog.log && \
    chown hids:hids /app/logs/watchdog.log && \
    chmod 666 /app/logs/watchdog.log

# Configurar SSH
RUN mkdir -p /home/hids/.ssh && \
    chown -R hids:hids /home/hids/.ssh && \
    chmod 700 /home/hids/.ssh

# Mudar para usuário não-root
USER hids

# Comando padrão
CMD ["python", "Api_watchdog/watchdog_service.py"]