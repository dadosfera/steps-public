from dadosfera.services.snowflake import get_snowpark_session
from snowflake.snowpark import functions as F
from typing import List, Dict
import logging
import json
import sys
import os

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

def save_data_in_snowflake(
    secret_id: str,
    table_identifier: str,
    snowflake_queries_object: Dict
) -> None:

    if len(snowflake_queries_object['queries']) > 1:
        raise Exception('The number of queries is greater than one')

    if len(snowflake_queries_object['post_actions']) > 0:
        raise Exception('The number of post_actions is greater than 0')

    session = get_snowpark_session(secret_id)
    df = session.sql(snowflake_queries_object['queries'][0])
    df.write.mode('overwrite').save_as_table(table_identifier)


def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    table_identifier = orchest.get_step_param('table_identifier')
    input_type = orchest.get_step_param('input_type')

    if input_type == "from_filepath":
        input_filepath = orchest.get_step_param("input_filepath")
        with open(input_filepath) as f:
            snowflake_queries_object = json.loads(f.read())

    elif input_type == "from_incoming_variable":
        incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        snowflake_queries_object = orchest.get_inputs()[incoming_variable_name]

    save_data_in_snowflake(
        secret_id=secret_id,
        table_identifier=table_identifier,
        snowflake_queries_object=snowflake_queries_object
    )

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    secret_id = config["secret_id"]
    input_filepath = config['input_filepath']
    table_identifier = config['table_identifier']

    with open(input_filepath,'r') as f:
        snowflake_queries_object = json.load(f)
    save_data_in_snowflake(
        secret_id=secret_id,
        table_identifier=table_identifier,
        snowflake_queries_object=snowflake_queries_object
    )

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
