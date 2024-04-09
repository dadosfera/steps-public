# Snowflake Flatten Columns

## Table of Contents

1. Introduction
2. Environment Setup
3. Process Structure and Features
4. User Interface and Validation Schema
5. Configuration Examples

## 1. Introduction

This guide details the procedure to create a data processing step aimed at flattening nested snowflake (object) columns within a dataset.

## 2. Environment Setup

### Dependencies

Install the required dependencies as listed in `requirements.txt`. Use the following commands:


Required dependencies are listed in the `requirements.txt` file. To install them, run:

```bash
sudo apt-get update
pip3 install pyOpenSSL --upgrade
pip3 install boto3 awscli chardet requests anybase32 pandas snowflake-snowpark-python

aws codeartifact login --tool pip --domain dadosfera --domain-owner 611330257153 --region us-east-1 --repository dadosfera-pip
pip3 install dadosfera==1.5.0 dadosfera_logs==1.0.3
```

## 3. Process Structure and Features

### Core Functions

- `auto_discovery_valid_flatten_columns()`: Identifies columns suitable for flattening, specifically those in the JSON format: {"key_1":"value_1", "key_2":"value_2"}.
- `get_keys()`: Extracts and returns all unique keys from an object column as an array.
- `get_column_flatten_select_expressions()`: Generates SQL SELECT expressions for flattening each identified column. Returns a tuple of a list of expressions and None if valid, or an empty list with the column name if flattening isn't feasible, retaining the original column in the dataset.
- `flatten_data`: Orchestrates the above functions to generate and apply SQL expressions for data flattening. Retains non-flattened columns in the dataset.
- `snowflake_flatten_columns`: Accepts a dataframe and target columns, applies the generated SQL expressions, and returns a modified dataframe.

### Preprocessing functions:

- `_drop_columns_that_match_at_least_prefix()`: Drops columns matching a specified prefix, useful for excluding irrelevant data. (e.g, PROPERTY_HS_DEAL_ENTERED_STAGE_IN_.....).
- `_remove_prefixes_from_columns`: Strips specified prefixes from column names to standardize naming conventions. (e.g, PROPERTY_HS_DEAL_ENTERED_STAGE_IN_CLOSED_WON -> HS_DEAL_ENTERED_STAGE_IN_CLOSED_WON)
- Additionally, users can specify columns to be removed via the columns_to_remove parameter.

## 4. Esquema de Interface de Usuário e Validação

The `.uischema.json` file defines the user interface for data flow configuration, while the `.schema.json` file sets the validation schema for input data.

## 5. Configuration Examples

#### Required parameters
- `secret_id`: Identifier for Snowflake credentials (e.g., prd/root/snowflake_credentials/dadosferafin).
- `incoming_variable_name`: Variable name from the preceding step containing the base table query.
- `auto_discovery_flatten_mode`: Enables automatic detection of columns for flattening.
- `columns_to_flatten`: Explicitly specify columns to flatten if auto_discovery_flatten_mode is disabled.

#### Optional parameters

- `before_apply_operations`: Configurations for preliminary data modifications, including:
    - `columns_to_remove`: List of columns to be excluded.
    - `column_prefixes_to_remove`:  Identifies columns for exclusion based on prefixes.
    - `remove_prefixes_from_columns`: Specifies prefixes to be removed from column names.

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
1. **Utility of Preprocessing Functions**: Preprocessing functions are essential for managing datasets with potentially thousands of columns, especially when the limit of supported columns in Snowflake (2000) might be exceeded. These functions allow for the removal of unnecessary data, reducing the dataset to a manageable size before flattening.
2. **Function Application Order**: Currently, functions are applied in the following sequence:
    a. `column_prefixes_to_remove`
    b. `columns_to_remove`
    c. `remove_prefix_from_columns`

Consider this order when configuring your data processing step. Future updates may introduce more flexible sequencing options, enabling users to specify the exact order of operations.

This documentation is designed to provide a clear, step-by-step guide for setting up and executing the data flattening process, ensuring that users can efficiently manage their HubSpot deal progression data within Snowflake environments.
