from dadosfera.services.snowflake import get_snowpark_session
from snowflake.snowpark import functions as F
from snowflake.snowpark.exceptions import SnowparkClientException
from typing import Dict
import logging
import json
import sys
import os

# Configuração avançada de logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

def validate_inputs(secret_id: str, table_name: str, row_data: dict):
    """
    Valida os inputs antes de prosseguir com a operação no Snowflake.
    """
    if not secret_id:
        raise ValueError("O secret_id não foi fornecido.")
    if not table_name:
        raise ValueError("O nome da tabela não foi fornecido.")
    if not isinstance(row_data, dict) or not row_data:
        raise ValueError("Os dados da linha (row_data) estão inválidos ou vazios.")
    logger.debug(f"Inputs validados: secret_id={secret_id}, table_name={table_name}, row_data={row_data}")

def create_session(secret_id: str):
    """
    Cria uma sessão no Snowflake.
    """
    try:
        session = get_snowpark_session(secret_id)
        logger.info("Sessão Snowflake criada com sucesso.")
        return session
    except Exception as e:
        logger.error(f"Falha ao criar sessão Snowflake: {e}")
        raise

def check_table_exists(session, table_name: str):
    """
    Verifica se uma tabela existe no Snowflake.
    """
    try:
        session.table(table_name).show()
        logger.info(f"Tabela '{table_name}' encontrada no Snowflake.")
    except SnowparkClientException as e:
        logger.error(f"Tabela '{table_name}' não encontrada: {e}")
        raise ValueError(f"A tabela '{table_name}' não existe. Certifique-se de criá-la antes de inserir dados.")

def insert_row(session, table_name: str, row_data: dict):
    """
    Insere uma linha em uma tabela no Snowflake.
    """
    try:
        df = session.create_dataframe([row_data], schema=list(row_data.keys()))
        df.write.save_as_table(table_name, mode="append")
        logger.info(f"Linha inserida com sucesso na tabela '{table_name}': {row_data}")
    except Exception as e:
        logger.error(f"Erro ao inserir dados na tabela '{table_name}': {e}")
        raise

def write_row_to_snowflake(secret_id: str, table_name: str, row_data: dict):
    """
    Gerencia o fluxo completo de escrita de uma linha no Snowflake.
    """
    validate_inputs(secret_id, table_name, row_data)
    session = None
    try:
        session = create_session(secret_id)
        check_table_exists(session, table_name)
        insert_row(session, table_name, row_data)
    finally:
        if session:
            session.close()
            logger.info("Sessão Snowflake encerrada.")

def orchest_handler():
    import orchest
    try:
        logger.debug("Iniciando handler para Orchest...")
        secret_id = orchest.get_step_param('secret_id')
        table_name = orchest.get_step_param('table_name')
        raw_input_data = orchest.get_inputs()
        logger.debug(f"Dados de entrada do step anterior: {raw_input_data}")

        data_registration = list(raw_input_data.values())[1][0]  # Ajuste conforme o formato esperado
        write_row_to_snowflake(secret_id, table_name, data_registration)
    except Exception as e:
        logger.error(f"Erro no handler Orchest: {e}")
        raise

def script_handler():
    try:
        logger.debug("Iniciando handler para script...")
        if len(sys.argv) != 2:
            raise ValueError("Forneça a configuração requerida no formato JSON.")
        config_json = sys.argv[1]
        config = json.loads(config_json)

        secret_id = config["secret_id"]
        table_name = config['table_name']
        data_registration = config['data_registration']

        write_row_to_snowflake(secret_id, table_name, data_registration)
    except Exception as e:
        logger.error(f"Erro no handler Script: {e}")
        raise

if __name__ == "__main__":
    if ORCHEST_STEP_UUID:
        logger.info("Executando como Orchest Step")
        orchest_handler()
    else:
        logger.info("Executando como script standalone")
        script_handler()
