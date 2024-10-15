from dadosfera.services.snowflake import get_snowpark_session
from snowflake.snowpark import functions as F
from snowflake.snowpark.exceptions import SnowparkSQLException
from typing import List, Dict
import logging
import json
import sys
import os

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


import snowflake.snowpark as snowpark
from snowflake.snowpark import DataFrame
from snowflake.snowpark.functions import any_value, col

def auto_discovery_valid_flatten_columns(data_frame):
    def _is_object(data_frame, column_name):
        try:
            data_frame.select(F.object_keys(F.parse_json(column_name)))
        except SnowparkSQLException as e:
            return False
        return True

    columns_to_flatten = []
    for column in data_frame.columns:
        if _is_object(data_frame, column):
            logger.info(f'{column} is valid for flattening')
            columns_to_flatten.append(column)
    return columns_to_flatten

def get_keys(data_frame, column_name):
    keys = (
        data_frame
        .select(F.object_keys(F.parse_json(column_name)).alias(column_name))
        .selectExpr(f'ARRAY_UNION_AGG({column_name}) as KEYS')
        .collect()
    )
    return json.loads(keys[0].KEYS)

def normalized_column_name(keys):
    invalid_symbols = [
        " ", "\t", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "+", "=", 
        "{", "}", "[", "]", ":", ";", "'", "\"", "|", "\\", "<", ">", ",", ".", 
        "/", "?", "!", "~", "`"
    ]
    for symbol in invalid_symbols:
        keys = keys.replace(symbol, "_")
    return keys


def replace_quotes(string):
    return string.replace("\"","")

def get_column_flatten_select_expressions(data_frame, column_name):
    try:
        keys = get_keys(data_frame, column_name)

        select_expr = []

        for key in keys:

            new_column_name = replace_quotes(
                f"{normalized_column_name(column_name)}__{normalized_column_name(key)}"
            )
            
            select_expr.append(
                f'parse_json({column_name}):"{key}"::string as {new_column_name}'
            )
        return select_expr, None
    except SnowparkSQLException as e:
        return [], column_name

def flatten_data(data_frame, columns_to_flatten):
    flatten_expressions = []
    invalid_columns = []

    for column in columns_to_flatten:
        select_expr, invalid_column = get_column_flatten_select_expressions(
            data_frame, column)

        flatten_expressions.extend(select_expr)

        if invalid_column:

            logger.warning(f'Unable to flatten: {invalid_column}')
            invalid_columns.append(invalid_column)

    select_expr = flatten_expressions + data_frame.columns

    logger.info(f'Select Expr before filtering: {select_expr}')
    return [
        column
        for column in select_expr
        if column not in columns_to_flatten or column in invalid_columns
    ]

def snowflake_flatten_columns(
        df: DataFrame,
        columns_to_flatten: List[str]
    ) -> List[str]:


    select_expr = flatten_data(df, columns_to_flatten)
    logger.info(f'Select Expr after filtering: {select_expr}')
    return df.select_expr(*select_expr)

def _drop_columns_that_match_at_least_prefix(data_frame, column_prefixes):
    prefixes = []
    for prefix in column_prefixes:
        for column in data_frame.columns:
            if str(column).startswith(prefix):
                prefixes.append(column)

    logger.info(prefixes)
    return data_frame.drop(*list(set(prefixes)))

def _remove_prefixes_from_columns(data_frame, column_prefixes):
    prefixes_to_remove = sorted(column_prefixes, key=len, reverse=True)

    for prefix in prefixes_to_remove:
        for column in data_frame.columns:
            if column.startswith(prefix):
                data_frame = data_frame.with_column_renamed(column, column.replace(prefix, ""))
    return data_frame

def _before_apply_function_operations(
        secret_id,
        snowflake_queries_object,
        operations
    ):
    session = get_snowpark_session(secret_id)
    df = session.sql(snowflake_queries_object['queries'][0])

    logger.info(operations)
    columns_to_remove = operations.get(
        'columns_to_remove', []
    )
    if len(columns_to_remove) > 0:
        logger.info('Removing columns provided by the user')
        df = df.drop(*columns_to_remove)

    columns_prefixes_to_remove = operations.get(
        'column_prefixes_to_remove', []
    )
    if len(columns_prefixes_to_remove) > 0:
        logger.info('Removing columns that matches prefixes')
        df = _drop_columns_that_match_at_least_prefix(df, columns_prefixes_to_remove)


    remove_prefix_from_columns = operations.get(
        'remove_prefix_from_columns', []
    )
    if len(remove_prefix_from_columns) > 0:
        logger.info('Removing Prefixes from column names')
        df = _remove_prefixes_from_columns(df, remove_prefix_from_columns)

    return df

def _post_apply(df):
    return df.queries


def orchest_handler():
    import orchest
    secret_id = orchest.get_step_param('secret_id')
    incoming_variable_name = orchest.get_step_param('incoming_variable_name', None)

    before_apply_operations = orchest.get_step_param('before_apply_operations', {})
    output_variable_name = orchest.get_step_param('output_variable_name')
    snowflake_queries_object = orchest.get_inputs()[incoming_variable_name]

    df = _before_apply_function_operations(
        secret_id=secret_id,
        snowflake_queries_object=snowflake_queries_object,
        operations=before_apply_operations
    )

    logger.info(f'Queries: {df.queries}')

    auto_discovery_flatten_mode = orchest.get_step_param('auto_discovery_flatten_mode', False)
    if auto_discovery_flatten_mode:
        columns_to_flatten = auto_discovery_valid_flatten_columns(df)
    else:
        columns_to_flatten = orchest.get_step_param('columns_to_flatten')

    if columns_to_flatten is None:
        logger.error('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')
        raise Exception('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')

    if len(columns_to_flatten) == 0:
        logger.error('No Valid Columns To Flatten Found')
        raise Exception('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')

    df = snowflake_flatten_columns(df, columns_to_flatten)
    queries = _post_apply(df)

    logger.info(f'Adding the following output to orchest: {queries}')
    orchest.output(data=queries, name=output_variable_name)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    secret_id = config.get('secret_id')
    incoming_variable_name = config.get('incoming_variable_name', None)
    before_apply_operations = config.get('before_apply_operations', {})

    output_variable_name = config.get('output_variable_name')

    with open(input_filepath) as f:
        snowflake_queries_object = json.loads(f.read())

    df = _before_apply_function_operations(
        secret_id=secret_id,
        snowflake_queries_object=snowflake_queries_object,
        columns_to_remove=columns_to_remove_before_apply,
        columns_prefixes_to_remove=columns_prefixes_to_remove_before_apply_operation
    )
    logger.info(f'Queries: {df.queries}')

    auto_discovery_flatten_mode = config.get('auto_discovery_flatten_mode', True)
    if auto_discovery_flatten_mode:
        columns_to_flatten = auto_discovery_valid_flatten_columns(df)
    else:
        columns_to_flatten = config.get('columns_to_flatten')

    if columns_to_flatten is None:
        logger.error('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')
        raise Exception('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')

    if len(columns_to_flatten) == 0:
        logger.error('No Valid Columns To Flatten Found')
        raise Exception('If auto_discovery_flatten_columns_mode is turnoff, you should provide the columns to flatten')

    df = snowflake_flatten_columns(df, columns_to_flatten)
    queries = _post_apply(df)

    with open(output_filepath,'w') as f:
        f.write(json.dumps(queries))

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
