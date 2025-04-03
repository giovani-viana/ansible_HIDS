import os
import subprocess

def run_command(command):
    """Executa um comando no shell e verifica erros."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {command}")
        print(f"Detalhes: {e}")
        exit(1)

def block_traffic(ip):
    """Bloqueia todo o tráfego para um IP específico."""
    print(f"Bloqueando todo o tráfego para o IP {ip}...")
    run_command(f"sudo iptables -A OUTPUT -d {ip} -j REJECT")
    print(f"Tráfego para o IP {ip} bloqueado com sucesso!")

def limit_traffic(ip, limit="10/s", burst="20"):
    """Aplica uma limitação de tráfego para um IP específico."""
    print(f"Aplicando limitação de tráfego para o IP {ip}, limite {limit}, rajada {burst}...")
    run_command(f"sudo iptables -A OUTPUT -p tcp -d {ip} -m limit --limit {limit} --limit-burst {burst} -j ACCEPT")
    run_command(f"sudo iptables -A OUTPUT -p tcp -d {ip} -j REJECT")
    print(f"Limitação de tráfego aplicada com sucesso para o IP {ip}!")

def main(action, ip):
    # Verificar se o script está sendo executado como root
    if os.geteuid() != 0:
        print("Este script precisa ser executado como root!")
        exit(1)

    # Verificar se o iptables está instalado
    if not os.path.exists("/sbin/iptables"):
        print("O iptables não está instalado neste sistema.")
        exit(1)

    # Executar a ação de mitigação com base no parâmetro fornecido
    if action == "block":
        block_traffic(ip)
    elif action == "limit":
        limit_traffic(ip)
    else:
        print("Ação inválida! Use 'block' ou 'limit'.")

if __name__ == "__main__":
    # Exemplo de chamada com parâmetros fornecidos manualmente
    # Esses valores podem ser substituídos por dados recebidos de uma API externa
    action_to_perform = "block"       # Ação a ser executada: 'block' ou 'limit'
    ip_to_mitigate = "192.168.1.100"  # Substitua pelo IP recebido

    # Chamar a função principal com os parâmetros
    main(action=action_to_perform, ip=ip_to_mitigate)