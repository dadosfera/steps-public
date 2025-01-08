# Conector de Dados - Contact2Sale (C2S)

Este passo (step) realiza a coleta de leads a partir da API da Contact2Sale, 
respeitando a lógica de Full Load (quando não há histórico de execução) 
e Incremental (quando já existe um registro de data/hora de atualização).

## Step `get_data_from_cs2` 

### Visão Geral

Este conector interage com o endpoint:

```
  GET https://api.contact2sale.com/integration/leads
```
R
respeitando:

- Paginação via parâmetros page e perpage.
- Limite de 10 requisições por minuto (para evitar bloqueio pela API).
- Filtro incremental através de updated_gte, que retorna apenas leads atualizados a partir de uma data/hora específica.

Caso não exista histórico de execução (primeira vez), é feita uma carga completa (full load), coletando todos os registros disponíveis. Em execuções subsequentes, o script obtém apenas os registros que foram atualizados após a última data registrada.

### Arquivos e Variáveis Principais

- get_data_from_c2s.py: Arquivo Python com a lógica de coleta, onde ficam as funções:
    - get_last_update()
    - save_last_update()
    - fetch_data()
    - find_max_updated_at()
    - main()
- last_update.json: Arquivo que armazena a última data/hora de atualização (formato ISO 8601 com Z no final). Se este arquivo não existir (ou estiver inválido), o script faz Full Load.

#### Variáveis de Configuração:

- BASE_URL: URL base para a API (ex.: https://api.contact2sale.com/integration/leads).
- TOKEN: Token de autenticação (Bearer Token).
- PER_PAGE: Quantidade de registros por página.
- MAX_REQ_PER_MINUTE: Quantidade máxima de requisições a cada 60s (evita rate limit).
- LAST_UPDATE_PATH: Caminho para o arquivo last_update.json.

### Como Funciona o Fluxo

1. Verificação do Arquivo de Histórico (`last_update.json`)

- O script chama get_last_update() para verificar se existe uma data/hora salva.
    - Se não existir, considera `None` → Full Load.
    - Se existir (ex.: `"2024-12-27T10:46:28Z"`), o script usa esse valor → Incremental.

2. Coleta dos Dados (`fetch_data()`)

- Monta a requisição com parâmetros de paginação (`page`, `perpage`).
- Se estiver em modo incremental, adiciona `updated_gte` ao params.
- Executa requisições em loop até alcançar o total de registros informado pela API (data['meta']['total']).
- Respeita o limite de 10 requisições/minuto, realizando `time.sleep(60)` quando atinge esse valor.

3. Processamento Local e Salvamento

- Todos os leads são acumulados em `all_results`.
- Se houver algum destino (ex.: Snowflake), o script converte a lista de dicionários em DataFrame e grava na tabela configurada.

4. Atualização do `updated_gte`

- Ao final da coleta, o script chama `find_max_updated_at()` para descobrir a maior data/hora de atualização nos leads retornados.
- Se encontrar um valor (`new_updated_gte`), ele é salvo em last_update.json pela função `save_last_update()`.

5. Execução Futura

- Na próxima execução, a função `get_last_update()` encontra esse valor
    → o script busca apenas registros atualizados após esse timestamp, reduzindo a carga e tempo de processamento.
    
### Como Executar

1. Instale Dependências

- Verifique se possui requests, json, time e outras bibliotecas padrão do Python 3.
- Caso vá gravar no Snowflake, instale snowflake-connector-python ou snowflake-snowpark-python.

2. Configure as Variáveis

- Ajuste BASE_URL para https://api.contact2sale.com/integration/leads.
- Defina TOKEN com um Bearer Token válido na Contact2Sale.
- Ajuste LAST_UPDATE_PATH, se desejar um caminho diferente (padrão: last_update.json).

4. Rode o Script

- Na primeira execução, o script não encontrará last_update.json e fará o full load.
- Ao final, criará (ou atualizará) o arquivo last_update.json com o maior updated_at.
- Na segunda execução, fará o modo incremental (apenas dados atualizados após a data armazenada).

### Pontos de Atenção

1. Número de Registros

- Caso existam milhares de leads, o script pode demorar para terminar a carga inicial devido ao rate limit (10 requisições/minuto).
- Ajuste PER_PAGE para o máximo permitido pela API (ex.: 50).

2. Formato de Data

- A Contact2Sale retorna datas no padrão ISO8601 (sem milissegundos).
- A função find_max_updated_at() está preparada para strings do tipo YYYY-MM-DDTHH:MM:SSZ.

3. Persistência

- Após obter leads, você pode salvá-los em um arquivo local (JSON), banco de dados ou Snowflake.
- Verifique se há necessidade de tratamento de duplicatas ou merges de atualização.

4. Erros e Exceções

- Se a API retornar erro (ex.: 401, 500), o script fará log do problema e a exceção será levantada.
- Em caso de problemas de rede ou timeouts, revise a lógica de retry/timeout no requests.get().