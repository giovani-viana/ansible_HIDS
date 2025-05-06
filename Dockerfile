FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    openssh-client \
    ansible \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios necessários
RUN mkdir -p /app/state /app/logs /app/scripts && chmod 777 /app/logs

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

# Criar usuário não-root
RUN useradd -m -s /bin/bash hids
RUN chown -R hids:hids /app

# Configurar SSH
RUN mkdir -p /home/hids/.ssh
RUN chown -R hids:hids /home/hids/.ssh
RUN chmod 700 /home/hids/.ssh

# Mudar para usuário não-root
USER hids

# Comando padrão
CMD ["python", "Api_watchdog/watchdog_service.py"]