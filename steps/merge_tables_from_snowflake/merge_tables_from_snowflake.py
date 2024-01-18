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

def merge_tables_from_snowflake(
        secret_id: str,
        snowflake_queries_left: Dict,
        snowflake_queries_right: Dict,
        columns_to_merge: List[str]
    ) -> List[str]:
    import pandas as pd
    session = get_snowpark_session(secret_id)
    target = session.sql(snowflake_queries_left['queries'][0]).to_pandas()
    source = session.sql(snowflake_queries_right['queries'][0]).to_pandas()
    df = target.merge(source, left_on=columns_to_merge[0], right_on=columns_to_merge[1]) 
    return df

def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    left_table = orchest.get_step_param('left_table')
    right_table = orchest.get_step_param('right_table')
    columns_to_merge = orchest.get_step_param('columns_to_merge')
    output_variable_name = orchest.get_step_param('output_variable_name')
    
    snowflake_queries_left = orchest.get_inputs()[left_table]
    snowflake_queries_right = orchest.get_inputs()[right_table]
    
    queries = merge_tables_from_snowflake(
        secret_id=secret_id,
        snowflake_queries_left=snowflake_queries_left,
        snowflake_queries_right=snowflake_queries_right,
        columns_to_merge=columns_to_merge
    )
    
    logger.info(f'Adding the following output to orchest: {queries}')
    orchest.output(data=queries, name=output_variable_name)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    secret_id = config.get('secret_id')
    input_filepath_left = config.get('input_filepath_left')
    input_filepath_right = config.get('input_filepath_right')
    output_filepath = config.get('output_filepath')
    columns_to_merge = config.get('columns_to_merge')
    
    with open(input_filepath_left) as f:
        snowflake_queries_left = json.loads(f.read())

    with open(input_filepath_right) as f:
        snowflake_queries_right = json.loads(f.read())
        
    queries = merge_tables_from_snowflake(
        secret_id=secret_id,
        snowflake_queries_left=snowflake_queries_left,
        snowflake_queries_right=snowflake_queries_right,
        columns_to_merge=columns_to_merge
    )
    with open(output_filepath,'w') as f:
        f.write(json.dumps(queries))

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
