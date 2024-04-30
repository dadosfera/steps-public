# Step de Mesclar Tabelas no Snowflake

Este STEP permite mesclar tabelas alvo no Snowflake usando dados de entrada fornecidos de algum processo anterior ou mesmo de outro ativo de dados no Snowflake. O STEP possui uma feature que procura compatibilizar os DataTypes entre as colunas das tabelas Source e Target.

## Recursos

- Mescla tabelas do Snowflake com base em colunas especificadas.
- Suporta execução como parte de uma orquestração ou como um script autônomo.
- Flexibilidade na configuração das tabelas de origem e de destino, bem como das colunas usadas para a fusão.

## Requisitos

- Python 3.x
- Biblioteca do Snowflake
- Biblioteca Pandas
- Biblioteca Snowpark

## Uso

### Execução como parte de uma Orquestração

Quando executado como parte de uma orquestração, este STEP espera os seguintes parâmetros:

- `secret_id`: As credenciais do cliente no Snowflake.
- `source_table`: O nome da tabela de origem no Snowflake ou os dados de saída de um step anterior em formato DataFrame do Pandas, em lista de dicionários ou arquivos .csv, .json e .parquet.
- `target_table`: O nome da tabela de destino no Snowflake.
- `source_on`: As colunas na tabela de origem para a junção.
- `target_on`: As colunas na tabela de destino para a junção.

### Execução como um Script Autônomo

Para executar o STEP como um script autônomo, forneça os parâmetros de configuração em um arquivo JSON. Aqui está um exemplo de configuração:

```json
{
    "secret_id": "snowflake_secret_id",
    "source_table": "nome_da_tabela_origem",
    "target_table": "nome_da_tabela_destino",
    "source_on": ["coluna1", "coluna2"],
    "target_on": ["coluna3", "coluna4"]
}
```

Salve a configuração acima em um arquivo (por exemplo, `config.json`) e execute o script da seguinte forma:

```
python merge_tables_from_snowflake.py config.json
```

Substitua `config.json` pelo caminho do seu arquivo de configuração.

## Saída

Esse step `merge_tables_from_snowflake` deve ser utilizado como step final de uma pipeline, assim sendo, a variável **source_table** pode receber o mesmo nome da variável de saída do step anterior, se este step produzir um Pandas DataFrame, ou objeto que pode ser transformado em DataFrame.
