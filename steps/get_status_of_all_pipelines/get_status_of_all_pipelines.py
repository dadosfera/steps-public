import pandas as pd
from typing import Dict, Union, Literal, List
import os
import sys
import json
import logging
from dadosfera.services.maestro import get_status_of_all_pipelines, get_token

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def orchest_handler():
    import orchest

    maestro_base_url = orchest.get_step_param('maestro_base_url')
    output_type = orchest.get_step_param('output_type')

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
    pipelines = get_status_of_all_pipelines(
        maestro_base_url=maestro_base_url,
        token=token
    )

    if output_type == 'to_outgoing_variable':
        output_variable_name = orchest.get_step_param('output_variable_name')
        output = [
            {
                'key': 'pipelines',
                'file_name': 'pipelines',
                'file_content': pipelines
            }
        ]pipelines_status
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
    pipelines = get_status_of_all_pipelines(
        maestro_base_url=maestro_base_url,
        token=token
    )

    df = pd.DataFrame(pipelines)
    df.to_parquet(output_filepath, 'fastparquet')

if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
