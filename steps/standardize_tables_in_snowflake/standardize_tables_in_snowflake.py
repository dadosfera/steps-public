from dadosfera.services.snowflake import get_snowpark_session
import sys
import json
import logging
import os
import pandas as pd
from typing import Dict,  List, Optional

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_snowflake_table(
    secret_id: str,
    table_identifier: str
) -> List[str]:
    session = get_snowpark_session(secret_id)
    df = session.table(table_identifier)
    return df.queries


def save_data_from_file(
    secret_id: str,
    table_identifier: str,
    file_path: str,
    file_format: str,
    file_format_params: Optional[Dict[str, str]] = None,
):
    session = get_snowpark_session(secret_id)
    session.use_schema("PUBLIC")

    logger.info("Creating temporary stage")
    create_temp_stage = "create or replace temporary stage my_internal_stage"
    session.sql(create_temp_stage).collect()

    logger.info("Putting objects into Snowflake Internal Stage")
    transformed_tbl_identifier = table_identifier.replace(
        '"', "").replace(".", "_")
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

        result_df = reader.csv(
            f"@my_internal_stage/{transformed_tbl_identifier}")

    logger.info("Saving data to snowflake")
    result_df.write.mode("overwrite").save_as_table(table_identifier)


def read_records(mapping_file_path):
    """ Lê o file JSON e retorna o conteúdo como uma lista de dicionários. """
    try:
        with open(mapping_file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"file {mapping_file_path} não encontrado.")
        return []
    except json.JSONDecodeError:
        print(f"Erro ao decodificar o file {mapping_file_path}.")
        return []


def standardize_tables_in_snowflake(secret_id, mapping_file_path):
    mappeds = read_records(mapping_file_path)
    for mapped in mappeds:
        if not mapped["its_manual_registry"]:
            spark_df = get_snowflake_table(secret_id, mapped["source"])
            df = spark_df.toPandas()
            new_df = pd.DataFrame({
                "firstname": df[mapped.get("firstname")],
                "surname": df[mapped.get("surname")],
                "company": df[mapped.get("company")],
                "phone": df[mapped.get("phone")],
                "cellphone": df[mapped.get("cellphone")],
                "email": df[mapped.get("email")],
                "address": df[mapped.get("address")],
                "birth_date": df[mapped.get("birth_date")],
                "site": df[mapped.get("site")],
                "id": df[mapped.get("id")],
                "source": mapped.get("source")
            })

            if mapped["owner_is_column"]:
                new_df["owner"] = df[mapped["owner"]]
            else:
                new_df["owner"] = mapped["owner"]

            file_path = "TEMP_JSON_LINES.json"
            new_df.to_json(file_path, orient='records', lines=True)
            schema, name = mapped["source"]
            new_table_name = f"{schema.upper()}.STANDARDIZED_{name.upper()}"
            save_data_from_file(secret_id=secret_id,
                                file_path=file_path, file_format="json", table_identifier=new_table_name)


def orchest_handler():
    import orchest
    mapping_file_path = orchest.get_step_param('mapping_file_path')
    secret_id = orchest.get_step_param('secret_id')
    standardize_tables_in_snowflake(
        mapping_file_path=mapping_file_path,
        secret_id=secret_id
    )


def script_handler():
    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    input_filepath = config['input_filepath']
    table_identifier = config['table_identifier']
    secret_id = config['secret_id']

    with open(input_filepath, 'r') as f:
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
