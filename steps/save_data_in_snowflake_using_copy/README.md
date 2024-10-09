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

## Exemplos de pipeline 
Para salvar o arquivo processado em tabela no Snowflake existe dois procedimentos compatíveis até o momento:  
- arquivo  
- variável (sem documentação por enquanto)  
### Salvando em arquivo  
O arquivo deve ser salvo no código fonte  
[MAIN CONFIGURARION:](./main_configuration.png)  
- **SecretsManager** secret_id  
- **Table Identifier** PUBLIC.TABLE_NAME  
- **Input Type**   

SecretsManager, deve ser consultado entrando em contato com o suporte   
Table Identifier é o nome da tabela e por padrão é: PUBLIC.TB_NOME_DA_TABELA  
  Nesse caso vamos usar o Schema como PUBLIC. Vale lembrar, que no Snowflake dentro da Dadosfera os tipos de **Schema** são:  
    - **PUBLIC** (raw, landing-zone)  
    - **STAGING**  
    - **CURATED**  
Input Type pode ser `from_filepath` ou `from_incoming_variable`  

No nosso exemplo vamos usar `from_filepath`, pois buscamos os dados que serão salvos no Snowflake diretamente do arquivo salvo no código fonte que será setado em:  
[INPUT CONFIGURATION](./input_configuration.png)   
- **Input Filepath**  
- **File Format**  
- **Delimiter**  
- **Skip Header**  

OBS:  
Não existe ainda a opção de setar o parse_header pelo Input. Por default a Dadosfera considera parse_header igual a `True`, o que significa que a primeira linha será o header.  
Para alterar esse parâmetro procurar por `parse_header` no arquivo save_data_in_snowflake_using_copy.py e setar a variável para `False`.  

### [Em desenvolvimento]
Para usar os dados processado na pipeline deve ser usado 
- `from_incoming_variable`
Porém ainda estamos trabalhando nesse sentido.

## Dicas 
- Pode ser importante entender os arquivos save_data_in_snowflake_using_copy.py.uischema.json e save_data_in_snowflake_using_copy.py.schema.json  
- Esses dois arquivos são fundamentais para entendimento de como o step vai ser interagido ao setar MAIN CONFIGURARION e INPUT CONFIGURATION  
- Para consultar o nome da secret, entre em contato com o suporte.

