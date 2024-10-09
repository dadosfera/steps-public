from snowflake.snowpark import Session
from dadosfera.services.snowflake import get_snowpark_session
import sys
import json
import logging
import os
import pandas as pd
from typing import Dict, List, Optional
from functools import reduce

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def save_data_from_objects(
    secret_id: str, table_identifier: str, objects: List[Dict[str, str]]
):
    try:
        session = get_snowpark_session(secret_id)
        session.use_schema("PUBLIC")

        logger.info("Creating temporary stage")
        create_temp_stage = "create or replace temporary stage my_internal_stage"
        session.sql(create_temp_stage).collect()

        logger.info("Parsing Objects into Dataframe")
        dfs = [pd.DataFrame(_object["file_content"]) for _object in objects]

        logger.info("Combining the data")
        result_pdf = reduce(lambda x, y: pd.concat([x, y], axis=0), dfs)
        result_pdf.to_parquet("temp", engine="fastparquet")

        logger.info("Putting objects into Snowflake Internal Stage")
        transformed_tbl_identifier = table_identifier.replace('"', "").replace(".", "_")
        put_command = f"PUT file://temp @my_internal_stage/{transformed_tbl_identifier}"
        session.sql(put_command).collect()

        logger.info("Reading Parquet File")
        result_df = session.read.parquet(f"@my_internal_stage/{transformed_tbl_identifier}")

        logger.info("Saving data to snowflake")
        result_df.write.mode("overwrite").save_as_table(table_identifier)
    finally:
        os.remove('temp')


def save_data_from_file(
    secret_id: str,
    table_identifier: str,
    file_path: str,
    file_format: str,
    file_format_params: Optional[Dict[str, str]] = None,
):
    import orchest
    session = get_snowpark_session(secret_id)
    session.use_schema("PUBLIC")

    logger.info("Creating temporary stage")
    create_temp_stage = "create or replace temporary stage my_internal_stage"
    session.sql(create_temp_stage).collect()

    logger.info("Putting objects into Snowflake Internal Stage")
    transformed_tbl_identifier = table_identifier.replace('"', "").replace(".", "_")
    put_command = (
        f"PUT file://{file_path} @my_internal_stage/{transformed_tbl_identifier}"
    )
    session.sql(put_command).collect()

    logger.info("Reading Parquet File")

    if file_format == "parquet":
        result_df = session.read.parquet(
            f"@my_internal_stage/{transformed_tbl_identifier}"
        )
    elif file_format == "json":
        result_df = session.read.option("INFER_SCHEMA", "true").json(
            f"@my_internal_stage/{transformed_tbl_identifier}"
        )
    elif file_format == "csv":
        reader = session.read.option("INFER_SCHEMA", "true")

        delimiter = file_format_params.get("delimiter")
        if delimiter is not None:
            reader = reader.option("field_delimiter", delimiter)

        skip_header_option = file_format_params.get("skip_header_option")
        if skip_header_option is not None:
            reader = reader.option("skip_header_option", skip_header_option)

        parse_header = True # deveria vim dos parâmetros do Input (mudar json Schema)
        reader = reader.option("parse_header", parse_header)

        result_df = reader.csv(f"@my_internal_stage/{transformed_tbl_identifier}")

    logger.info("Saving data to snowflake")
    result_df.write.mode("overwrite").save_as_table(table_identifier)


def orchest_handler():
    import orchest

    input_type = orchest.get_step_param("input_type")
    table_identifier = orchest.get_step_param("table_identifier")
    secret_id = orchest.get_step_param("secret_id")

    if input_type == "from_filepath":
        input_filepath = orchest.get_step_param("input_filepath")
        file_format = orchest.get_step_param("file_format")
        if file_format == "csv":
            file_format_params = orchest.get_step_param("csv_file_format")
        else:
            file_format_params = {}

        save_data_from_file(
            secret_id=secret_id,
            table_identifier=table_identifier,
            file_path=input_filepath,
            file_format=file_format,
            file_format_params=file_format_params,
        )

    elif input_type == "from_incoming_variable":
        incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        objects = orchest.get_inputs()[incoming_variable_name]
        save_data_from_objects(
            secret_id=secret_id, table_identifier=table_identifier, objects=objects
        )


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)
    secret_id = config["secret_id"]
    input_type = config["input_type"]
    table_identifier = config["table_identifier"]

    if input_type == "from_filepath":
        input_filepath = config["input_filepath"]
        file_format = config["file_format"]

        if file_format == "csv":
            file_format_params = config["csv_file_format"]
        else:
            file_format_params = {}

        save_data_from_file(
            secret_id=secret_id,
            table_identifier=table_identifier,
            file_path=input_filepath,
            file_format=file_format,
            file_format_params=file_format_params,
        )


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
