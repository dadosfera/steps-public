# Validação de Dados com JSON Schema

Este step fornece um script para validação de dados JSON contra um schema definido (de acordo com um `schema.json`, utilizando a biblioteca `jsonschema` para garantir que os dados estejam conformes com o formato especificado. O script pode ser executado diretamente via linha de comando ou como parte de um pipeline do **Orchest**.

## Responsável pela criação desse step

Mikael Akihitto Hirata Iwamoto

## Funcionalidades

1. **Validação de Dados**: Validação de um arquivo JSON com base em um schema JSON, utilizando o `Draft7Validator`.
2. **Suporte ao Orchest**: O script pode ser executado como um passo dentro de pipelines do Orchest, manipulando dados de steps anteriores e enviando os resultados para o próximo.
3. **Execução via Script**: Pode ser executado diretamente como um script, recebendo dados JSON de entrada e gerando um arquivo de saída com os resultados da validação.

## Estrutura dos Arquivos

- **`main.py`**: Script principal que realiza a validação de dados, com suporte para execução no Orchest ou como um script isolado.
- **`data_validation.py.schema.json`**: Arquivo de schema JSON utilizado para validar os dados de entrada. Este arquivo precisa ser personalizado conforme a estrutura dos dados que deseja validar.
- **`output_data.json`**: Arquivo gerado após a execução do script contendo os resultados da validação.

## Requisitos

- Python 3.7+
- Bibliotecas Python:
  - `json`
  - `jsonschema`
  - `logging`
  - `os`
  - `sys`
  - `orchest` (opcional, para execução no Orchest)



## Execução

### 1. Como Script

Para executar o script diretamente, forneça o JSON de entrada como argumento de linha de comando:

```bash
python data_validation.py '{"chave": "valor"}'
```

O resultado será salvo em um arquivo `output_data.json`, contendo o status da validação e possíveis erros.

### 2. Como Step do Orchest

Quando executado no contexto de um pipeline do Orchest, o script irá carregar os dados do step anterior e, após a validação, passar os resultados para o próximo step. O script verifica a variável de ambiente `ORCHEST_STEP_UUID` para identificar se está sendo executado no Orchest.

## Detalhes da Execução

### Carregamento de Schema

A função `load_schema` carrega o schema JSON a partir de um arquivo especificado. Se o arquivo não for encontrado ou estiver inválido, uma exceção será lançada e registrada no log.

### Validação de Dados

A função `validate_data` utiliza o `Draft7Validator` para verificar a conformidade dos dados com o schema. Caso a validação falhe, os erros são registrados e retornados em formato de lista.

### Entrada e Saída

- **Entrada**:
  - Como script: Recebe os dados JSON a partir da linha de comando.
  - Como Orchest Step: Recebe os dados de entrada a partir do step anterior.
  
- **Saída**:
  - Gera um arquivo `output_data.json` com o status da validação e eventuais erros.

## Logging

O script utiliza o módulo `logging` para fornecer informações detalhadas sobre o progresso e quaisquer erros encontrados durante a execução. O nível de logging está definido como `DEBUG` para fornecer o máximo de detalhes.

## Exemplo de Uso

1. Salve um schema JSON no arquivo `main.py.schema.json`.
2. Execute o script passando os dados de entrada no formato JSON.
   
```bash
python data_validation.py '{"name": "John Doe", "age": 30}'
```

3. O arquivo `output_data.json` conterá a seguinte estrutura:

```json
{
    "input_data": {
        "name": "John Doe",
        "age": 30
    },
    "data_status": true,
    "error_list": []
}
```
