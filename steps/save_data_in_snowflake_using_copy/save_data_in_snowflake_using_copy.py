from snowflake.snowpark import Session
from dadosfera.services.snowflake import get_snowpark_session
import sys
import json
import logging
import os
import pandas as pd
from typing import Dict, Union, List
from functools import reduce

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def save_objects_in_snowflake_using_copy(
    secret_id: str,
    objects: List[Dict[str, Union[str, bytes]]],
    table_identifier: str
) -> None:

    try:
        session = get_snowpark_session(secret_id)
        session.use_schema('PUBLIC')
        dfs = [pd.DataFrame(_object['file_content']) for _object in objects]
        result_pdf = reduce(lambda x, y: pd.concat([x, y], axis=0), dfs)
        result_pdf.to_parquet('temp', engine='fastparquet')

        transformed_tbl_identifier = table_identifier.replace('"', '').replace('.', '_')
        create_temp_stage = "create or replace temporary stage my_internal_stage"
        session.sql(create_temp_stage).collect()

        put_command = f"PUT file://temp @my_internal_stage/{transformed_tbl_identifier}"
        session.sql(put_command).collect()
        result_df = session.read.parquet(f"@my_internal_stage/{transformed_tbl_identifier}")
        result_df.write.mode('overwrite').save_as_table(table_identifier)
    finally:
        os.remove('temp')

def orchest_handler():
    import orchest
    table_identifier = orchest.get_step_param('table_identifier')
    incoming_variable_name = orchest.get_step_param('incoming_variable_name')
    secret_id = orchest.get_step_param('secret_id')
    objects = orchest.get_inputs()[incoming_variable_name]
    save_objects_in_snowflake_using_copy(
        objects=objects,
        table_identifier=table_identifier,
        secret_id=secret_id
    )

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    input_filepath = config['input_filepath']
    table_identifier = config['table_identifier']
    secret_id = config['secret_id']

    with open(input_filepath,'r') as f:
        objects = json.load(f)

    save_objects_in_snowflake_using_copy(
        objects=objects,
        table_identifier=table_identifier,
        secret_id=secret_id
    )

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
