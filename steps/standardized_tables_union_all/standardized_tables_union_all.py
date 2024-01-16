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


def get_union_all_query(secret_id: str, table_prefix: str) -> str:
    session = get_snowpark_session(secret_id)

    # Listar tabelas que começam com 'STANDARDIZED_'
    query_list_tables = f"SHOW TABLES LIKE '{table_prefix}%'"
    df_tables = session.sql(query_list_tables).collect()

    # Construir a query de UNION ALL
    query_parts = []
    for table in df_tables:
        table_name = table['name']
        query_parts.append(f"SELECT * FROM {table_name}")

    union_all_query = " UNION ALL ".join(query_parts)

    return union_all_query


def standardized_tables_union_all(secret_id: str, view_name: str, union_all_query: str):
    session = get_snowpark_session(secret_id)
    create_view_query = f"CREATE OR REPLACE VIEW {view_name} AS {union_all_query}"
    session.sql(create_view_query).collect()
    logger.info(f"View {view_name} created successfully.")


def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    union_all_query = get_union_all_query(secret_id, "STANDARDIZED_")
    standardized_tables_union_all(
        union_all_query, "VW_STANDARDIZED_MDM_BASE", union_all_query)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    secret_id = os.getenv('secret_id')
    union_all_query = get_union_all_query(secret_id, "STANDARDIZED_")
    standardized_tables_union_all(
        union_all_query, "VW_STANDARDIZED_MDM_BASE", union_all_query)


if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
