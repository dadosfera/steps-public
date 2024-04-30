from dadosfera.services.snowflake import get_snowpark_session
from snowflake import snowpark
import pandas as pd
from typing import List, Dict, Union
import logging
import json
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set logger level to DEBUG
logger.setLevel(logging.DEBUG)

# Get ORCHEST_STEP_UUID from environment variable
ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


def merge_tables_from_snowflake(
        secret_id: str,
        source_table: Union[pd.DataFrame, str, List[Dict[str, Union[str, bytes]]]],
        target_table: str,
        source_on: List[str],
        target_on: List[str]
    ) -> None:
    """Merge tables from Snowflake using provided queries and columns."""
    
    # Get Snowpark session
    session = get_snowpark_session(secret_id)
    session.use_schema(target_table.split(".")[0])
    
    # Execute Snowflake query to load target table
    target = session.table(target_table)

    # Check the type of source_table and convert to snowpark DataFrame if necessary
    if isinstance(source_table, pd.DataFrame):
        schema = get_target_schema(target)
        source = session.create_dataframe(source_table, schema)
    elif isinstance(source_table, list):
        schema = get_target_schema(target)
        source = session.create_dataframe(source_table, schema)
    elif isinstance(source_table, str):
        source = session.table(source_table)
    else:
        raise ValueError("source_table must be table from snowflake, a pandas DataFrame or a list of dictionaries.")
    
    # Construct merge condition
    condition_clause = snowpark.functions.lit(True)
    for i, (source_col, target_col) in enumerate(zip(source_on, target_on)):
        condition_clause &= (target[target_col] == source[source_col])

    # Prepare update and insert clauses
    update_set_clause = {col: source[col] for col in source.columns if col in target.columns}
    insert_set_clause = {col: source[col] for col in source.columns}

    # Merge tables
    target.merge(
        source=source,
        join_expr=condition_clause,
        clauses=[
            snowpark.functions.when_matched().update(update_set_clause),
            snowpark.functions.when_not_matched().insert(insert_set_clause)
        ],
        statement_params={"ERROR_ON_NONDETERMINISTIC_MERGE": False}
    )

    
def orchest_handler():
    """Orchest handler for running as part of an orchestration."""
    
    import orchest
    
    # Get parameters from orchest
    secret_id = orchest.get_step_param('secret_id')
    source_table_name = orchest.get_step_param('source_table')
    target_table = orchest.get_step_param('target_table')
    source_on = orchest.get_step_param('source_on')
    target_on = orchest.get_step_param('target_on')
    try:
        source_table = orchest.get_inputs()[source_table_name]
    except KeyError:
        source_table = source_table_name
    
    # Merge tables
    merge_tables_from_snowflake(
        secret_id=secret_id,
        source_table=source_table,
        target_table=target_table,
        source_on=source_on,
        target_on=target_on
    )


def script_handler():
    """Script handler for running from command line with JSON configuration."""
    
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    
    # Load configuration from JSON
    config_json = sys.argv[1]
    config = json.loads(config_json)

    # Extract configuration parameters
    secret_id = config.get('secret_id')
    input_filepath_source = config.get('input_filepath_source')
    source_on = config.get('source_on')
    target_on = config.get('target_on')
    
    # Load source data from file
    if input_filepath_source.endswith('.csv'):
        source_table = pd.read_csv(input_filepath_source)
    elif input_filepath_source.endswith('.json'):
        source_table = pd.read_json(input_filepath_source)
    elif input_filepath_source.endswith('.parquet'):
        source_table = pd.read_parquet(input_filepath_source, engine='fastparquet')
    else:
        raise ValueError("input_filepath_source must be a path to a .csv, .json or .parquet file.")
        
    # Merge tables
    merge_tables_from_snowflake(
        secret_id=secret_id,
        source_table=source_table,
        target_table=config.get('target_table'),
        source_on=source_on,
        target_on=target_on
    )

    
def get_target_schema(target):
    """Script to get the schema of the target table to handle datatypes transformation."""
    
    # Initialize an empty list to hold the schema fields
    schema_fields = []

    # Iterate over the target schema fields
    for tgt_field in target.schema.fields:
        # Get the field name and datatype
        field_name = tgt_field.column_identifier.name
        field_datatype = str(tgt_field.datatype).split('(')[0].strip()

        # Map the datatype string to the corresponding Snowpark datatype
        if field_datatype == 'StringType':
            datatype = snowpark.types.StringType()
        elif field_datatype == 'IntegerType':
            datatype = snowpark.types.IntegerType()
        elif field_datatype == 'ArrayType':
            datatype = snowpark.types.ArrayType()
        elif field_datatype == 'VariantType':
            datatype = snowpark.types.VariantType()
        elif field_datatype == 'TimestampType':
            datatype = snowpark.types.TimestampType()
        elif field_datatype == 'DateType':
            datatype = snowpark.types.DateType()
        # Create a StructField with the field name and datatype
        struct_field = snowpark.types.StructField(field_name, datatype)

        # Add the StructField to the schema fields list
        schema_fields.append(struct_field)

    # Create a StructType with the schema fields and return schema
    return snowpark.types.StructType(schema_fields)


if __name__ == "__main__":

    # Determine whether running as Orchest step or script
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()