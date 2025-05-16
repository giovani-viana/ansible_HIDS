FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    openssh-client \
    ansible \
    sqlite3 \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -s /bin/bash hids

# Criar diretórios necessários e configurar permissões
RUN mkdir -p /app/state /app/logs /app/scripts /app/data && \
    chown -R hids:hids /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/state && \
    chmod -R 777 /app/data

# Copiar arquivos da aplicação
COPY --chown=hids:hids Api_watchdog /app/Api_watchdog
COPY --chown=hids:hids rules_playbook.yml /app/
COPY --chown=hids:hids scripts /app/scripts/
COPY --chown=hids:hids ansible.cfg /app/

# Configurar diretório de trabalho
WORKDIR /app

# Instalar dependências Python
RUN pip install requests python-dotenv

# Tornar os scripts executáveis
RUN chmod +x /app/Api_watchdog/dynamic_inventory.py && \
    chmod +x /app/Api_watchdog/watchdog_service.py

# Configurar SSH
RUN mkdir -p /home/hids/.ssh && \
    chown -R hids:hids /home/hids/.ssh && \
    chmod 700 /home/hids/.ssh

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    CHECK_INTERVAL=15

# Mudar para usuário não-root
USER hids

# Comando padrão
CMD ["python", "Api_watchdog/watchdog_service.py"]