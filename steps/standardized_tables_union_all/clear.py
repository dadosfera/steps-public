import subprocess
import os


def docker_compose_down():
    print("Executando 'docker compose down' para parar e remover os contêineres...")
    subprocess.run(['docker', 'compose', 'down'])


def remove_docker_images():
    print("Obtendo a lista de imagens Docker criadas pelo Docker Compose...")
    result = subprocess.run(
        ['docker', 'compose', 'config', '--services'], capture_output=True, text=True)
    services = result.stdout.strip().split('\n')
    current_dir = os.path.basename(os.getcwd())
    for service in services:
        # Construir o nome da imagem
        image_name = f"{current_dir}-{service}"
        print(f"Removendo a imagem {image_name}...")
        subprocess.run(['docker', 'rmi', image_name])


def main():
    try:
        docker_compose_down()
        remove_docker_images()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main()
