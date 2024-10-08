# Documentação de Salvar Objetos no Snowflake

O Snowflake é uma plataforma de armazenamento de dados baseada em nuvem. O esquema fornecido facilita a função de salvar objetos no Snowflake, permitindo que os usuários especifiquem os parâmetros necessários.

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)

## Sobre o projeto

O esquema fornecido define a estrutura para um payload JSON destinado a salvar objetos específicos no Snowflake. Ele descreve os parâmetros necessários para efetuar a operação com precisão.

## Pré-requisitos

- Acesso à plataforma Snowflake.
- Conhecimento dos objetos específicos que você deseja salvar.

## Configuração

### Parâmetros:

- **incoming_variable_name**: Especifica o nome da variável que contém os dados que serão copiados para o Snowflake.

- **secret_id**: Representa o secret_id que será utilizado para recuperar as credenciais do Snowflake.

- **table_identifier**: Refere-se ao nome da tabela onde os objetos serão salvos. Exemplo: PUBLIC.TABLE_NAME.

_Observação_: É fundamental fornecer corretamente o nome da variável de entrada e o identificador da tabela para garantir que os objetos sejam salvos corretamente.


## Examplos de configuração

```json
{
  "incoming_variable_name": "upstream_output_variable_name",
  "secret_id": "nome_da_secret",
  "table_identifier": "PUBLIC.TABLE_NAME"
}
```

## Exemplos de pipeline salvando em arquivo
Quando é escolhido a opção de salvar em arquivo, salvamos os arquivo no código fonte  
Em [MAIN CONFIGURARION](./main_configuration.png) vamos setar os campos: secret_id, table_name e input_type  
O nome da tabela é por padrão: PUBLIC.TB_NAME  
Nesse caso, como estamos "puxando" os dados de um arquivo que foi salvo no código fonte vamos selecionar from_filepath  
Como foi escolhido from_filepath o nome do arquivo, deverá ser passado em [INPUT CONFIGURATION](./input_configuration.png)   


Para consultar o nome da secret, entre em contato com o suporte.

