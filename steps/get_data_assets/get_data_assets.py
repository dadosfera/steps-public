import pandas as pd
from typing import Dict, Union, Literal, List
import os
import sys
import json
import logging
from dadosfera.services.maestro import get_data_assets, get_token

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def orchest_handler():
    import orchest

    maestro_base_url = orchest.get_step_param('maestro_base_url')
    additional_params_array = orchest.get_step_param('additional_params')
    output_type = orchest.get_step_param('output_type')

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
    data_assets = get_data_assets(
        maestro_base_url=maestro_base_url,
        token=token,
        additional_params=additional_params
    )

    if output_type == 'to_outgoing_variable':
        output_variable_name = orchest.get_step_param('output_variable_name')
        output = [
            {
                'key': 'data_assets',
                'file_name': 'data_assets',
                'file_content': data_assets
            }
        ]
        orchest.output(data=output, name=output_variable_name)
    elif output_type == 'to_filepath':
        output_filepath = orchest.get_step_param('output_filepath')
        df = pd.DataFrame(data_assets)
        df.to_parquet(output_filepath, 'fastparquet')

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    maestro_base_url = config['maestro_base_url']
    output_filepath = config['output_filepath']
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
    data_assets = get_data_assets(
        maestro_base_url=maestro_base_url,
        token=token,
        additional_params=additional_params
    )

    df = pd.DataFrame(data_assets)
    df.to_parquet(output_filepath, 'fastparquet')

if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
