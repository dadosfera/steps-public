from dadosfera.services.snowflake import get_snowpark_session
from typing import List
import logging
import json
import sys
import os

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

def get_snowflake_table(
        secret_id: str,
        table_identifier: str
    ) -> List[str]:
    session = get_snowpark_session(secret_id)
    df = session.table(table_identifier)
    return df.queries

def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    table_identifier = orchest.get_step_param('table_identifier')
    output_type = orchest.get_step_param('output_type')
    queries = get_snowflake_table(
        secret_id=secret_id,
        table_identifier=table_identifier
    )
    if output_type == 'to_filepath':
        output_filepath = orchest.get_step_param('output_filepath')
        with open(output_filepath,'w') as f:
            f.write(json.dumps(queries))
    elif output_type == 'to_outgoing_variable':
        logger.info(f'Adding the following output to orchest: {queries}')
        output_variable_name = orchest.get_step_param('output_variable_name')
        orchest.output(data=queries, name=output_variable_name)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    bucket_name = config.get('secret_id')
    prefix = config.get('table_identifier')
    output_filepath = config.get('output_filepath')
    queries = get_snowflake_table(bucket_name=bucket_name, prefix=prefix)
    with open(output_filepath,'w') as f:
        f.write(json.dumps(queries))

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
