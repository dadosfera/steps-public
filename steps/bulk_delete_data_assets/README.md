# Get Data Assets Documentation

[Maestro](https://maestro.dadosfera.ai) is an API platform, offering a range of solutions for data management. The given schema facilitates bulk deletion of data assets via its API, allowing users to specify various parameters.

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)

## Sobre o projeto

The provided schema defines the structure for a JSON payload meant for bulk deletion of data assets in Maestro. This is crucial for users looking to maintain a streamlined dataset by removing redundant or unwanted data in bulk, ensuring efficient data management.

## Pré-requisitos

- An username and password from Dadosfera.
- Permissions to delete the data assets
- Proper understanding of the data assets you wish to delete.

## Configuração

### Parâmetros:

- **maestro_base_url**: This represents the base URL for Maestro's API. Allowed values include "https://maestro.dadosfera.ai" and "https://maestro.stg.dadosfera.ai".
  
- **output_variable_name**: The name of the variable where the result will be stored.

- **additional_params**: An array of parameters that act as filters for determining which data assets will be deleted. Each parameter consists of a `key` (filter name) and `value` (filter criteria).

_Observação_: Ensure that you're selecting the right base URL and setting the output variable appropriately to prevent accidental data loss or misdirection.

![](https://files.readme.io/c4bfa0f-image.png)

### Referências

- Maestro API Documentation
