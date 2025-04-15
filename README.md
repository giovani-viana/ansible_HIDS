# Sistema de Monitoramento e Mitigação com Ansible (HIPS)

Este é um sistema de monitoramento que utiliza Ansible para aplicar regras de mitigação baseadas em IPs obtidos de uma API.

## Pré-requisitos

- Docker e Docker Compose instalados
- Git instalado
- Acesso à API de monitoramento

## Estrutura do Projeto

ansible_HIPS/
├── Api_watchdog/
│ ├── watchdog_service.py
│ └── ansible-watchdog.service
├── scripts/
│ ├── block_https.sh
│ └── limit_https.sh
├── ansible.cfg
├── docker-compose.yml
├── Dockerfile
├── inventory.ini
├── requirements.txt
└── rules_playbook.yml

## Instalação e Configuração

1. **Clone o repositório**
   ```bash
   git clone [URL_DO_REPOSITORIO]
   cd ansible_HIPS
   ```

2. **Configure o arquivo de ambiente**
   
   Crie um arquivo `requirements.txt` com as dependências Python:
   ```
   requests>=2.25.1
   ```

3. **Configure a URL da API**
   
   Edite o arquivo `docker-compose.yml` e atualize a variável de ambiente:
   ```yaml
   environment:
     - API_URL=http://sua-api-real.com/ips
   ```

4. **Configure o Ansible**
   
   Verifique se o arquivo `ansible.cfg` está configurado corretamente:
   ```ini
   [defaults]
   inventory = inventory.ini
   private_key_file = ../.ssh/ansible
   ```

5. **Prepare os scripts de mitigação**
   
   Certifique-se que os scripts em `scripts/` têm permissão de execução:
   ```bash
   chmod +x scripts/*.sh
   ```

## Execução

1. **Construa e inicie o container**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Verifique os logs**
   ```bash
   docker-compose logs -f
   ```

## Monitoramento

- **Verificar status do serviço**
  ```bash
  docker-compose ps
  ```

- **Verificar logs do watchdog**
  ```bash
  docker-compose logs -f ansible_watchdog
  ```

## Comandos Úteis

- **Parar o serviço**
  ```bash
  docker-compose down
  ```

- **Reiniciar o serviço**
  ```bash
  docker-compose restart
  ```

- **Executar o playbook manualmente**
  ```bash
  docker-compose exec ansible_watchdog ansible-playbook rules_playbook.yml
  ```

## Troubleshooting

1. **Serviço não inicia**
   - Verifique se a URL da API está correta
   - Verifique os logs do container
   - Confirme se as permissões dos scripts estão corretas

2. **Playbook falha ao executar**
   - Verifique se os scripts em `scripts/` têm permissão de execução
   - Confirme se o container tem acesso à rede host
   - Verifique os logs do Ansible

3. **API não responde**
   - Confirme se a URL da API está acessível
   - Verifique se o formato da resposta da API está correto
   - Verifique se há problemas de rede

## Configurações Avançadas

1. **Ajustar intervalo de verificação**
   
   O intervalo padrão é de 5 minutos. Para alterar, modifique a variável `check_interval` em `Api_watchdog/watchdog_service.py`.

2. **Configurar regras personalizadas**
   
   Edite os scripts em `scripts/` para personalizar as regras de mitigação.

3. **Configurar logs**
   
   Os logs são armazenados em `watchdog.log`. Configure o nível de log em `Api_watchdog/watchdog_service.py`.

## Segurança

- O sistema requer privilégios elevados para executar regras iptables
- Mantenha as chaves SSH e credenciais seguras
- Monitore regularmente os logs em busca de atividades suspeitas

## Suporte

Para reportar problemas ou sugerir melhorias, abra uma issue no repositório.