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

## Logs
Logs provide detailed information about the API calls:
- `DEBUG`: Logs the request URL, parameters, and the full response JSON.
- `INFO`: Confirms successful requests.
- `ERROR`: Captures and logs any request failures.
