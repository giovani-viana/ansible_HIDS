# 🛡️ Sistema de Mitigação de Ataques HIPS

Sistema automatizado de mitigação de ataques utilizando Ansible para gerenciar regras de firewall em dispositivos IoT.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Monitoramento](#monitoramento)
- [Solução de Problemas](#solução-de-problemas)
- [Segurança](#segurança)

## 🎯 Visão Geral

Este sistema monitora continuamente uma API de detecção de ataques e, quando detecta um ataque, aplica automaticamente regras de mitigação nos dispositivos IoT afetados utilizando Ansible. O sistema é containerizado e pode ser facilmente implantado em qualquer ambiente que suporte Docker.

## 🔧 Requisitos

- Docker e Docker Compose
- Python 3.9+
- Acesso SSH aos dispositivos IoT
- Chave SSH para autenticação nos dispositivos

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://seu-repositorio/ansible_HIPS.git
cd ansible_HIPS
```

2. Crie o arquivo `.env` com as configurações necessárias:
```bash
cp .env.example .env
```

3. Edite o arquivo `.env` com suas configurações:
```env
API_URL=http://seu-servidor:5050
API_USERNAME=seu_usuario
API_PASSWORD=sua_senha
SSH_USER=pi
PRIVATE_KEY_FILE=/home/hids/.ssh/id_rsa
```

4. Construa e inicie o container:
```bash
docker-compose up -d --build
```

## ⚙️ Configuração

### Configurações do Ansible

O arquivo `ansible.cfg` contém as configurações principais do Ansible. As configurações mais importantes são:

```ini
[defaults]
private_key_file = /home/hids/.ssh/ansible_key
host_key_checking = False
inventory = /app/Api_watchdog/dynamic_inventory.py
```

### Scripts de Mitigação

Os scripts de mitigação estão localizados no diretório `scripts/`:

- `block_https.sh`: Bloqueia tráfego HTTPS
- `restore_https.sh`: Restaura tráfego HTTPS
- `reset_iptables.sh`: Reseta regras do iptables
- `limit_https.sh`: Limita tráfego HTTPS

## 🎮 Uso

### Iniciar o Serviço

```bash
docker-compose up -d
```

### Verificar Logs

```bash
docker-compose logs -f
```

### Parar o Serviço

```bash
docker-compose down
```

## 📊 Monitoramento

O sistema gera logs em `/app/logs/watchdog.log` dentro do container. Para monitorar em tempo real:

```bash
docker-compose exec hips tail -f /app/logs/watchdog.log
```

### Métricas

O sistema registra métricas em `/app/state/metrics.json`, incluindo:
- IPs processados
- Bloqueios bem-sucedidos
- Falhas de bloqueio

## 🔍 Solução de Problemas

### Problemas Comuns

1. **Erro de Conexão SSH**
   - Verifique se a chave SSH está corretamente configurada
   - Confirme se o usuário SSH tem permissões adequadas

2. **Falha na Execução do Playbook**
   - Verifique os logs do Ansible
   - Confirme se os scripts de mitigação são executáveis

3. **Erro de Autenticação na API**
   - Verifique as credenciais no arquivo `.env`
   - Confirme se a API está acessível

### Comandos Úteis

```bash
# Verificar status do container
docker-compose ps

# Reiniciar o serviço
docker-compose restart

# Verificar logs de erro
docker-compose logs --tail=100 -f
```

## 🔒 Segurança

### Boas Práticas

1. **Chaves SSH**
   - Use chaves SSH específicas para o serviço
   - Mantenha as chaves privadas seguras
   - Não compartilhe chaves entre ambientes

2. **Credenciais da API**
   - Use credenciais fortes
   - Atualize regularmente as senhas
   - Não compartilhe credenciais entre ambientes

3. **Permissões de Arquivos**
   - Mantenha os scripts com permissões mínimas necessárias
   - Use o usuário não-root `hids` no container

### Recomendações

- Mantenha o sistema atualizado
- Monitore regularmente os logs
- Faça backup das configurações
- Implemente monitoramento externo

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes sobre nosso código de conduta e o processo para enviar pull requests.