# Get Connection Documentation

[Maestro](https://maestro.dadosfera.ai) is an API platform, offering a range of solutions for data management. The given schema facilitates bulk deletion of connection via its API, allowing users to specify various parameters.

## Summary

- [About the project](#sobre-o-projeto)
- [Prerequirements](#pré-requisitos)
- [Configuration](#configuração)

## About the project

The provided schema defines the structure for a JSON payload meant for bulk deletion of connections in Maestro. 

## Prerequirements

- An username and password from Dadosfera.
- Permissions to delete the connections
- Proper understanding of the connections you wish to delete.

## Configuration

### Parameteres:

- **maestro_base_url**: This represents the base URL for Maestro's API. Allowed values include "https://maestro.dadosfera.ai" and "https://maestro.stg.dadosfera.ai".
  
- **output_variable_name**: The name of the variable where the result will be stored.

- **additional_params**: An array of parameters that act as filters for determining which connections will be deleted. Each parameter consists of a `key` (filter name) and `value` (filter criteria).

_Note_: Ensure that you're selecting the right base URL and setting the output variable appropriately to prevent accidental data loss or misdirection.

![](https://files.readme.io/c4bfa0f-image.png)

### References

- Maestro API Documentation


#### Configuration Examples

## Getting Connection List

```json
{
  "maestro_base_url": "https://maestro.dadosfera.ai",
  "output_variable_name": "arbitrary_output_name",
  "additional_params": [
    {
      "key": "connection_id",
      "value": "1697139607788_k3m7eq3d_google-sheets-1.0.0"
    }
  ]
}
```
