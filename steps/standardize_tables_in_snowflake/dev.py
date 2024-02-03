import os
import socket
import subprocess


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_free_port(starting_port, max_attempts=1000):
    port = starting_port
    attempts = 0

    while attempts < max_attempts:
        if not is_port_in_use(port):
            print(f"Porta livre encontrada: {port}")
            return port
        print(f"Porta {port} está em uso. Procurando a próxima...")
        port += 1
        attempts += 1

    raise Exception(
        "Não foi possível encontrar uma porta livre após o número máximo de tentativas")


def parse_aws_profile(profile_name):
    aws_credentials_file = os.path.join(
        os.path.expanduser('~'), '.aws', 'credentials')
    aws_config_file = os.path.join(os.path.expanduser('~'), '.aws', 'config')

    if not os.path.exists(aws_credentials_file) or not os.path.exists(aws_config_file):
        raise Exception(
            "Arquivos de configuração e/ou credenciais da AWS não encontrados.")

    # Carregar as credenciais
    with open(aws_credentials_file, 'r') as file:
        credentials = {}
        current_profile = None
        for line in file:
            if line.startswith('[') and line.endswith(']\n'):
                current_profile = line[1:-2]
                credentials[current_profile] = {}

            elif '=' in line and current_profile:
                key, value = line.strip().split('=', 1)
                credentials[current_profile][key.strip()] = value.strip()

    # Carregar a configuração
    with open(aws_config_file, 'r') as file:
        config = {}
        current_profile = None
        for line in file:
            if line.startswith('[') and line.endswith(']\n'):
                current_profile = line[1:-2].replace('profile ', '')
                config[current_profile] = {}
            elif '=' in line and current_profile:
                key, value = line.strip().split('=', 1)
                config[current_profile][key.strip()] = value.strip()

    # Verificar se o perfil escolhido existe
    if profile_name not in credentials:
        raise Exception(
            f"Perfil '{profile_name}' não encontrado.")

    # Configurar as variáveis de ambiente
    os.environ['AWS_ACCESS_KEY_ID'] = credentials[profile_name]['aws_access_key_id']
    os.environ['AWS_SECRET_ACCESS_KEY'] = credentials[profile_name]['aws_secret_access_key']
    os.environ['AWS_DEFAULT_REGION'] = config['default']['region']

    print(
        f"Credenciais e configurações da AWS exportadas para o perfil: {profile_name}")
    return


def main():
    aws_profile = "default"  # Substitua pelo perfil desejado
    starting_port = 8501    # Substitua pela sua porta inicial

    try:
        parse_aws_profile(aws_profile)
        free_port = find_free_port(starting_port)
        print(f"Configurando a variável de ambiente PORT para {free_port}")
        os.environ['PORT'] = str(free_port)

        print("Executando o docker-compose...")
        subprocess.run(['docker', 'compose', 'up'])
        print(
            f"Docker Compose executado. Acessar em: http://localhost:{free_port}")

    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
