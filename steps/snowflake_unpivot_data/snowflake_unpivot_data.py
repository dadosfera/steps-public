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

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


def snowflake_unpivot_columns(
    secret_id: str,
    snowflake_queries_object: Dict,
    categorical_column_name: str,
    numerical_column_name: str,
    columns_to_unpivot: List[str],
) -> List[str]:
    if len(snowflake_queries_object["queries"]) > 1:
        raise Exception("The number of queries is greater than one")

    if len(snowflake_queries_object["post_actions"]) > 0:
        raise Exception("The number of post_actions is greater than 0")

    session = get_snowpark_session(secret_id)
    df = session.sql(snowflake_queries_object["queries"][0])
    df = df.unpivot(numerical_column_name, categorical_column_name, columns_to_unpivot)
    return df.queries


def orchest_handler():
    import orchest

    secret_id = orchest.get_step_param("secret_id")
    categorical_column_name = orchest.get_step_param("categorical_column_name")
    numerical_column_name = orchest.get_step_param("numerical_column_name")
    columns_to_unpivot = orchest.get_step_param("columns_to_unpivot")
    input_type = orchest.get_step_param("input_type")
    output_type = orchest.get_step_param("output_type")

    if input_type == "from_filepath":
        input_filepath = orchest.get_step_param("input_filepath")
        with open(input_filepath) as f:
            snowflake_queries_object = json.loads(f.read())

    elif input_type == "from_incoming_variable":
        incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        snowflake_queries_object = orchest.get_inputs()[incoming_variable_name]

    queries = snowflake_unpivot_columns(
        secret_id=secret_id,
        snowflake_queries_object=snowflake_queries_object,
        categorical_column_name=categorical_column_name,
        numerical_column_name=numerical_column_name,
        columns_to_unpivot=columns_to_unpivot,
    )

    if output_type == "to_filepath":
        output_filepath = orchest.get_step_param("output_filepath")
        with open(output_filepath, "w") as f:
            f.write(json.dumps(queries))
    elif output_type == "to_outgoing_variable":
        logger.info(f"Adding the following output to orchest: {queries}")
        output_variable_name = orchest.get_step_param("output_variable_name")
        orchest.output(data=queries, name=output_variable_name)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    secret_id = config.get("secret_id")
    categorical_column_name = config.get("categorical_column_name")
    numerical_column_name = config.get("numerical_column_name")
    columns_to_unpivot = config.get("columns_to_unpivot")

    with open(input_filepath) as f:
        snowflake_queries_object = json.loads(f.read())

    queries = snowflake_unpivot_columns(
        secret_id=secret_id,
        snowflake_queries_object=snowflake_queries_object,
        categorical_column_name=categorical_column_name,
        numerical_column_name=numerical_column_name,
        columns_to_unpivot=columns_to_unpivot,
    )
    with open(output_filepath, "w") as f:
        f.write(json.dumps(queries))


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
