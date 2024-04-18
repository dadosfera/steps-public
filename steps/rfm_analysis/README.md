```
# Análise RFM - Step

## Visão Geral
Este step realiza a análise RFM (Recência, Frequência, Valor Monetário) em uma tabela do banco de dados Snowflake. Ele calcula os escores RFM para cada cliente com base em seu comportamento de compra e os categoriza em diferentes tipos de clientes. Os resultados são armazenados em uma nova tabela e podem ser exportados para um arquivo ou passados como uma variável em um ambiente de orquestração.

## Requisitos
- Python 3.x
- Conector Python para Snowflake
- Plataforma de orquestração (opcional)

## Instalação
1. Instale os pacotes Python necessários:
   ```bash
   pip install <pacote-snowflake>
   ```

## Uso

### Executando como um Script
Para executar o script diretamente, forneça um arquivo de configuração no formato JSON contendo os parâmetros necessários:
```bash
python rfm_analysis.py config.json
```
Exemplo de `config.json`:
```json
{
  "secret_id": "<seu_id_secreto_snowflake>",
  "table_identifier": "<identificador_da_tabela_fonte>",
  "customer_id_col": "<coluna_de_identificação_do_cliente>",
  "date_col": "<coluna_de_datas>",
  "monetary_col": "<coluna_monetária>",
  "output_filepath": "<caminho_do_arquivo_de_saída>"
}
```

### Executando em um Ambiente de Orquestração
Se estiver integrando com uma plataforma de orquestração como Orchest, defina a variável de ambiente `ORCHEST_STEP_UUID` e forneça os parâmetros do step:
```bash
export ORCHEST_STEP_UUID=<uuid_do_step>
python rfm_analysis.py
```
Parâmetros do step:
Os seguintes parâmetros deverão ser fornecidos ao executar o script:
- `secret_id`: ID secreto do Snowflake
- `table_identifier`: Identificador da tabela fonte no Snowflake
- `customer_id_col`: Coluna contendo IDs dos clientes
- `date_col`: Coluna contendo datas de compra
- `monetary_col`: Coluna contendo valores monetários
- `output_type`: Tipo de saída ('to_filepath' ou 'to_outgoing_variable')
- `output_filepath`: Caminho do arquivo de saída (obrigatório se o output_type for 'to_filepath')
- `output_variable_name`: Nome da variável de saída (obrigatório se o output_type for 'to_outgoing_variable')

## Saída
O script cria um dataframe com os resultados da análise RFM. Além disso, ele pode exportar as consultas para um arquivo ou passá-las como uma variável em um ambiente de orquestração.

Esse step `rfm_analysis` é facilmente integrável com outros steps, e assim sendo, a variável **output_variable_name** deverá ter o mesmo nome da variável **input_variable_name** do step posterior. 

EX: Executando o step `save_data_in_snowflake` logo após o `rfm_analysis` estamos realizando a consulta que gera a tabela RFM e adicionando essa tabela no Snowflake. 

```
