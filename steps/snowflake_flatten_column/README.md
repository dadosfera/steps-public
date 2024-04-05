# Hubspot Create Deals Progression Fact Table

## Table of Contents

1. Introduction
2. Environment Setup
3. Step Structure and Features
4. User Interface and Validation Schema
5. Step Example Configuration

## 1. Introduction

This document outlines the process for creating the step responsible for flattening snowflake columns that
are objects.

## 2. Environment Setup

### Dependencies

Required dependencies are listed in the `requirements.txt` file. To install them, run:

```bash
sudo apt-get update
pip3 install pyOpenSSL --upgrade
pip3 install boto3 awscli chardet requests anybase32 pandas snowflake-snowpark-python

aws codeartifact login --tool pip --domain dadosfera --domain-owner 611330257153 --region us-east-1 --repository dadosfera-pip
pip3 install dadosfera==1.5.0 dadosfera_logs==1.0.3
```

## 3. Step Structure and features

### Main Functions of the process

- `auto_discovery_valid_flatten_columns()`: Identify which columns are valid for the flattening process. They should have the following format:
{"key_1":"value_1","key_2":"value_2"}
- `get_keys()`: Identify all distinct keys that exists on a column, if the column is an object and return it as an array.
- `get_column_flatten_select_expressions()`: Returns the select_expr that will be used for each column to be flattened into one or more columns, depending, especially, in the number of keys available in the column. This function returns a tuple containing either (a list of expressions, and None) if the expressions are valid, or return a tuple containing an empty list and the name of the column that couldn't be flattened to be kept as part of the new data frame.
- `flatten_data`: Receive the columns to flatten, orchestrate the functions above and returns the select expressions that will be used to flatten the data. Columns that were flattened are removed. Columns that it was not possible to apply the process are kept as part of the data_frame.
- `snowflake_flatten_columns`: Receives a dataframe and the columns to flatten. Apply the select expression and returns a dataframe.

### Preprocessing functions:

- `_drop_columns_that_match_at_least_prefix()`: Identify columns that matches a prefix provided by the user and drop it from the data_frame. It's useful when there are a lot of columns that are not going to be used and they have the same prefix (e.g, PROPERTY_HS_DEAL_ENTERED_STAGE_IN_.....).
- `_remove_prefixes_from_columns`: Remove a prefix of a column. (e.g, PROPERTY_HS_DEAL_ENTERED_STAGE_IN_CLOSED_WON -> HS_DEAL_ENTERED_STAGE_IN_CLOSED_WON)
- You may also provide a list of columns to remove using the columns_to_remove parameter.


## 4. Esquema de Interface de Usuário e Validação

The `.uischema.json` file defines the user interface for data flow configuration, while the `.schema.json` file sets the validation schema for input data.

## 5. Configuration

### Input Parameters

#### Required parameters
- `secret_id`: The ID of the Snowflake Secret (e.g., prd/root/snowflake_credentials/dadosferafin).
- `incoming_variable_name`: The name of the variable provided by the upstream step that contains the query that will be used as a base table for this step.
- `auto_discovery_flatten_mode`: Whether the columns to be flattened should be automatically discovered by the step.
- `columns_to_flatten`: If the auto_discovery_flatten_mode is not true, you should provide the columns that should be flattened.

#### Optional parameters

- `before_apply_operations`: Object containing either of the following options:
    - `columns_to_remove`: List of columns to remove.
    - `column_prefixes_to_remove`: List of prefixes to identify columns to remove.
    - `remove_prefixes_from_columns`: Prefixes to remove from column values.
    

### Step Example Configuration

#### Input Parameters
```json
{
  "auto_discovery_flatten_mode": true,
  "incoming_variable_name": "deals_table_0",
  "output_variable_name": "deals_table_1",
  "secret_id": "prd/root/snowflake_credentials/dadosferafin"
}
```


#### Input Table

| PROPERTY_MAIN_COMPANY                                                                                                    |
|---------------------------------------------------------------------------------------------------------------------------|
| {"Value":"Mapi", "Timestamp":"2023-02-17T03:32:56.965000Z", "Source":"AUTOMATION_PLATFORM", "Source ID":"enrollmentId:485901041046;actionExecutionIndex:0"} |

#### Output Table

#### Table with the field flattened

| MAIN_COMPANY__VALUE | MAIN_COMPANY__TIMESTAMP        | MAIN_COMPANY__SOURCE    | MAIN_COMPANY__SOURCEID                              |
|---------------------|-------------------------------|-------------------------|-----------------------------------------------------|
| Mapi                | 2023-02-17T03:32:56.965000Z   | AUTOMATION_PLATFORM     | enrollmentId:485901041046;actionExecutionIndex:0    |


#### Example for Hubspot Deals of input Parameters

```json
{
  "auto_discovery_flatten_mode": true,
  "before_apply_operations": {
    "column_prefixes_to_remove": [
      "PROPERTY_HS_DATE_ENTERED_",
      "PROPERTY_HS_DATE_EXITED_",
      "PROPERTY_HS_TIME_IN_",
      "PROPERTY_HS_V2_CUMULATIVE_TIME_IN_",
      "PROPERTY_HS_V2_DATE_ENTERED_",
      "PROPERTY_HS_V2_LATEST_TIME_IN_",
      "PROPERTY_HS_V2_DATE_EXITED_"
    ],
    "columns_to_remove": [
      "PROPERTIES",
      "PROPERTIES_VERSIONS"
    ],
    "remove_prefix_from_columns": [
      "PROPERTY_"
    ]
  },
  "incoming_variable_name": "deals_table_0",
  "output_variable_name": "deals_table_1",
  "secret_id": "prd/root/snowflake_credentials/dadosferafin"
}
```

#### Additional Notes
1. Why the proprocessing functions may be useful? I have added some preprocessing functions because flattening may exceed the amount of columns supported on snowflake (2000). When applying this step without them, we have exceeded this limit.
2. The functions are applied in the following order for now:
    a. column_prefixes_to_remove
    b. columns_to_remove
    c. remove_prefix_from_columns

Keep this in mid while you are configuring the step. In the feature, we may refactor this to be use as a list of step where the order in the list is used to identify which function should be applied first.
