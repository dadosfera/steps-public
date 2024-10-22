from typing import Dict, Union, Literal, List
import os
import sys
import json
import logging
from dadosfera.services.maestro import get_token, bulk_delete_connections

# Configuração de variáveis e logger
ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def orchest_handler():
    import orchest

    maestro_base_url = orchest.get_step_param('maestro_base_url')
    additional_params_array = orchest.get_step_param('additional_params')

    if additional_params_array is not None:
        additional_params = {
            param['key']: param['value'] for param in additional_params_array
        }
    else:
        additional_params = {}

    try:
        DADOSFERA_USERNAME = os.environ['DADOSFERA_USERNAME']
        DADOSFERA_PASSWORD = os.environ['DADOSFERA_PASSWORD']
    except KeyError as e:
        logger.error(
            "Please provied the env_vars DADOSFERA_USERNAME and "
            "DADOSFERA_PASSWORD. "
        )
        raise e

    token = get_token(
        maestro_base_url=maestro_base_url,
        email=DADOSFERA_USERNAME,
        password=DADOSFERA_PASSWORD,
    )
    bulk_delete_connections(
        maestro_base_url=maestro_base_url,
        token=token,
        additional_params=additional_params
    )


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    maestro_base_url = config['maestro_base_url']
    additional_params = config.get('additional_params', {})

    try:
        DADOSFERA_USERNAME = os.environ['DADOSFERA_USERNAME']
        DADOSFERA_PASSWORD = os.environ['DADOSFERA_PASSWORD']
    except KeyError as e:
        logger.error(
            "Please provied the env_vars DADOSFERA_USERNAME and "
            "DADOSFERA_PASSWORD. "
        )
        raise e

    token = get_token(
        maestro_base_url=maestro_base_url,
        email=DADOSFERA_USERNAME,
        password=DADOSFERA_PASSWORD,
    )
    bulk_delete_connections(
        maestro_base_url=maestro_base_url,
        token=token,
        additional_params=additional_params
    )


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()