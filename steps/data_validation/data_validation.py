import json
import logging
import os
import sys
from jsonschema import Draft7Validator, FormatChecker
from typing import Tuple, List

# Configuração de variáveis e logger
ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def load_schema(schema_file: str) -> dict:
    """
    Carrega o JSON SCHEMA de validação a partir de um arquivo.

    :param schema_file: Caminho para o arquivo JSON schema.
    :return: O schema JSON carregado.
    :raises: Exception se houver erro na leitura do arquivo.
    """
    try:
        with open(schema_file, 'r') as file:
            schema = json.load(file)
        return schema
    except FileNotFoundError:
        logger.error(f"Arquivo de schema {schema_file} não encontrado.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer o parse do arquivo JSON: {e}")
        raise


def validate_data(data: dict, schema: dict) -> Tuple[bool, List[str]]:
    """
    Valida os dados fornecidos contra o schema JSON.

    :param data: Os dados a serem validados.
    :param schema: O schema JSON para validação.
    :return: Tuple contendo o status (True se válido, False se inválido) 
             e uma lista de mensagens de erro, se houver.
    """
    try:
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        errors = list(validator.iter_errors(data))

        if not errors:
            logger.info("Dados válidos!")
            return True, []
        else:
            error_messages = [f"Erro de validação: {error.message}" for error in errors]
            logger.warning(f"Erros de validação encontrados: {error_messages}")
            return False, error_messages
    except Exception as e:
        logger.error(f"Erro ao validar os dados: {str(e)}")
        return False, [str(e)]


def orchest_handler() -> None:
    """
    Função de controle quando o script é executado dentro de um pipeline Orchest.
    Carrega os dados de entrada de um step anterior, valida os dados e os passa
    para o próximo step junto com o status e eventuais erros.
    """
    import orchest

    # Pegando dados do step anterior
    input_data_from_step = orchest.get_inputs()

    # Assumindo que o segundo item do dicionário é relevante (ajuste conforme necessário)
    input_data = list(input_data_from_step.values())[1]

    # Carregando o schema e validando os dados
    schema_file = os.path.basename(__file__) + '.schema.json'
    schema = load_schema(schema_file)
    data_status, error_list = validate_data(input_data, schema)

    # Empacotando os dados para o próximo step
    output_data = [input_data, data_status, error_list]

    # Enviando dados para o próximo step
    orchest.output(output_data, name="validated_data")


def script_handler() -> None:
    """
    Função de controle para execução direta como script. 
    Carrega os dados a partir de um arquivo de entrada em formato JSON, valida 
    os dados e salva o resultado em um arquivo de saída.
    """
    if len(sys.argv) != 2:
        logger.error("Forneça a configuração necessária no formato JSON como argumento.")
        raise ValueError("Por favor, forneça a configuração necessária em formato JSON.")

    input_json = sys.argv[1]

    try:
        # Carregando dados de entrada a partir do argumento de linha de comando
        input_data = json.loads(input_json)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer o parse do JSON de entrada: {e}")
        raise

    # Carregando schema e validando os dados
    schema_file = os.path.basename(__file__) + '.schema.json'
    schema = load_schema(schema_file)
    data_status, error_list = validate_data(input_data, schema)

    # Empacotando os dados para saída
    output_data = {
        "input_data": input_data,
        "data_status": data_status,
        "error_list": error_list
    }

    # Salvando os resultados em um arquivo JSON
    with open("output_data.json", "w") as outfile:
        json.dump(output_data, outfile, indent=4)
    logger.info("Processo concluído. Dados de saída salvos em 'output_data.json'.")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Executando como Orchest Step")
        orchest_handler()
    else:
        logger.info("Executando como script")
        script_handler()
