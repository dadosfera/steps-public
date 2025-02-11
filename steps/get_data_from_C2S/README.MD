# Contact2Sale API Connector Documentation

## Overview

This project provides a Step connector for interacting with the Contact2Sale API. It allows users to retrieve data from the API by specifying a path and query parameters, making it easy to integrate Contact2Sale's data into your workflows.

## Summary
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Examples](#examples)
- [Available GET Endpoints](#available-get-endpoints)


## Features
- Connects to the Contact2Sale API using a secure Bearer token.
- Dynamically specifies the endpoint path and query parameters.
- Logs requests and responses for easier debugging and traceability.
- Includes error handling for failed requests.

## Requirements
- Python
- Orchest pipeline for step parameter integration
- Contact2Sale API access with a valid token

## Setup

### Install Dependencies
Install the required Python packages:
```bash
pip install requests
```

### Environment Variables
Set the following environment variable:
- `C2S_PROLAR_TOKEN`: Your API authentication token.

## Usage

1. Define the API path (`c2s_path`) and query parameters (`params`) in your Orchest pipeline step.
2. Run the script to make the API request and fetch data.

## Examples

### Example 1: Fetch Leads Data
```json
{
    "c2s_path": "/leads",
    "params": {
        "page": 4
    }
}
```
The above example fetches leads data from the `/leads` endpoint with `page=4` as a query parameter.

### Example 2: Fetch Leads Data
```json
{
    "c2s_path": "/leads",
    "params": {
        "page": [1, 2, 3, 4, 5]
    }
}
```
The above example fetches leads data from the `/leads` endpoint with `page=1, 2, 3, 4, and 5` as query parameter.

### Example 3: Fetch Leads Data
```json
{
    "c2s_path": "/leads",
    "params": {}
}
```
The above example fetches leads data from the `/leads` endpoint without any query parameter.

## Logs
Logs provide detailed information about the API calls:
- `DEBUG`: Logs the request URL, parameters, and the full response JSON.
- `INFO`: Confirms successful requests.
- `ERROR`: Captures and logs any request failures.

## Available GET Endpoints

Below is a list of the GET endpoints available in the Contact2Sale API and their descriptions:

### Leads
1. **/leads**  
   Retrieves a list of leads with support for filters like date, status, and sorting.  
   **Optional Parameters:**
   - `page`: Page number.
   - `perpage`: Number of records per page (maximum 50).
   - `sort`: Sort order (`created_at`, `-created_at`, `updated_at`, `-updated_at`).
   - `last_update`: ISO 8601 timestamp for filtering updates after a specific time.
   - `created_gte`: ISO 8601 timestamp for filtering leads created after or on a specific date.
   - `created_lt`: ISO 8601 timestamp for filtering leads created before a specific date.
   - `updated_gte`: ISO 8601 timestamp for filtering updates after or on a specific date.
   - `updated_lt`: ISO 8601 timestamp for filtering updates before a specific date.
   - `status`: Filter by lead status (`novo`, `em_negociacao`, `convertido`, etc.).

2. **/leads/{id}**  
   Retrieves detailed information about a specific lead by ID.  

3. **/leads/{id}/tags**  
   Retrieves tags associated with a specific lead.  

4. **/distribution_queues/list_queues**  
   Retrieves a list of available distribution queues.  

5. **/tags**  
   Retrieves the list of tags associated with the company.  

### Sellers
1. **GET /sellers**  
   Retrieves a list of sellers in the system.  

### Companies
1. **GET /me**  
   Retrieves information about the user’s company.  


All the information about the endpoints can be found in the [C2S documentation](https://api.contact2sale.com/docs/api).