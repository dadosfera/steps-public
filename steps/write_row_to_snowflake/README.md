# README

## Overview

This step is designed to automate the process of inserting a row of data into a Snowflake table. It integrates with Orchest for pipeline management and can also run as a standalone script. The step includes robust input validation, error handling, and session management for Snowflake, ensuring reliable and traceable operations.

Key functionalities include:
1. Validating input parameters.
2. Establishing a Snowflake session.
3. Verifying the existence of a Snowflake table.
4. Inserting data into the specified table.
5. Supporting execution as an Orchest pipeline step or standalone script.

## Requirements

- **Dependencies**:
  - `dadosfera.services.snowflake` for Snowflake session management.
  - `snowflake.snowpark` for Snowflake operations.
  - `orchest` for pipeline integration.
- **Environment Variables**:
  - `ORCHEST_STEP_UUID`: Set by Orchest to determine the mode of execution.

- **Parameters**:
  - `secret_id`: A secret identifier for Snowflake authentication.
  - `table_name`: The target Snowflake table name.
  - `row_data`: A dictionary containing the row of data to insert.

## How It Works

The script can be executed in two modes:
1. **Orchest Pipeline Step**: Executes within an Orchest pipeline, retrieving parameters and input data dynamically.
2. **Standalone Script**: Accepts input via command-line arguments in JSON format.

---

### Execution Steps

#### **1. Input Validation**
   **Input**:
   - `secret_id`: A string representing the Snowflake secret.
   - `table_name`: A string for the target table name.
   - `row_data`: A dictionary with the data to insert.

   **Output**:
   - Logs indicating successful validation or errors.

#### **2. Create Snowflake Session**
   **Input**:
   - `secret_id`.

   **Output**:
   - A Snowflake session object.

#### **3. Check Table Existence**
   **Input**:
   - `session`: The Snowflake session object.
   - `table_name`: The name of the table to verify.

   **Output**:
   - Logs confirming the table exists or an error if it does not.

#### **4. Insert Data**
   **Input**:
   - `session`: The Snowflake session object.
   - `table_name`: The name of the target table.
   - `row_data`: The row of data to insert.

   **Output**:
   - Confirmation log on successful insertion or an error message.

#### **5. Cleanup**
   - Closes the Snowflake session after operations.

---

### How to Use

#### **Script Handler**

1. Prepare a JSON configuration file:
   ```json
   {
       "secret_id": "prd/root/snowflake_credentials/{client_name}",
       "table_name": "your_table_name",
       "data_registration": {
           "column1": "value1",
           "column2": "value2"
       }
   }
   ```

2. Run the script:
   ```bash
   python write_row_to_snowflake.py '{"secret_id": "prd/root/snowflake_credentials/{client_name}", "table_name": "your_table_name", "data_registration": {"column1": "value1", "column2": "value2"}}'
   ```

#### **Orchest Pipeline Step**

1. Configure the Orchest step parameters:
   - `secret_id`: Pass as step parameter.
   - `table_name`: Pass as step parameter.

2. Ensure the previous step in the pipeline provides `row_data` as part of its output.

3. Execute the pipeline.

---

### Logging

The script uses advanced logging for debugging and tracking:
- **DEBUG**: Tracks detailed operations and inputs.
- **INFO**: Confirms successful operations.
- **ERROR**: Captures and logs exceptions.

---

### Error Handling

The script includes error handling for:
1. Missing or invalid inputs.
2. Failed Snowflake session creation.
3. Missing tables in Snowflake.
4. Data insertion errors.

---

### Example Use Case

#### Input:
```json
{
    "secret_id": "snowflake_secret",
    "table_name": "user_data",
    "data_registration": {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
}
```

#### Output:
- Row successfully inserted into the `user_data` table.

---

### Who Created

mikael.iwamoto@dadosfera.io