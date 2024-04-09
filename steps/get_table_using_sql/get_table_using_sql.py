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

def snowflake_execute_sql(
        secret_id: str,
        sql_statement: str
    ) -> List[str]:
    session = get_snowpark_session(secret_id)
    df = session.sql(sql_statement)
    return df.queries

def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    table_identifier = orchest.get_step_param('table_identifier')
    sql_statement_from = orchest.get_step_param('sql_statement_from')

    if sql_statement_from == 'from_filepath':
        sql_filepath = orchest.get_step_param('sql_filepath', None)
        with open(sql_filepath) as f:
            sql_statement = f.read()

    elif sql_statement_from == 'from_text':
        sql_statement = orchest.get_step_param('sql_statement', None)

    output_type = orchest.get_step_param('output_type')
    queries = snowflake_execute_sql(
        secret_id=secret_id,
        sql_statement=sql_statement
    )

    if sql_statement is None:
        raise Exception('Please provide a sql statement')
    
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
