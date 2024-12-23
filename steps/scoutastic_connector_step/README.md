# Scoutastic Connector Step

Este STEP connector é dedicado à API Scoutastic, que permite extrair dados de várias rotas da API, alterando apenas parâmetros, funções de paginação e o destino dos dados.

## Entidades

O conector suporta a extração de dados das seguintes entidades:

[x] **Appointments**: Detalhes sobre compromissos e eventos, como agendamentos de partidas, treinamentos e reuniões.

[x] **Competitions**: Informações sobre competições, incluindo dados como nome da competição, temporada, equipes participantes e estatísticas relevantes.

[x] **Managers**: Dados sobre gestores e técnicos, incluindo informações pessoais, histórico de gestão e estatísticas de desempenho.

[x] **Matches**: Detalhes sobre partidas, incluindo data, hora, local, equipes envolvidas, resultados e estatísticas do jogo.

[x] **Players**: Informações sobre jogadores, incluindo dados pessoais, histórico de carreira, estatísticas de desempenho e status atual.

[x] **Players Missed**: Listas de jogadores ausentes em determinados eventos ou partidas, incluindo razões de ausência.

[x] **Transfers History**: Histórico de transferências de jogadores entre clubes, incluindo detalhes como data da transferência, valores envolvidos, clubes de origem e destino.

[x] **Teams**: Informações sobre as equipes, incluindo composição do elenco, treinadores, desempenho histórico e estatísticas atuais.

[x] **Reports**: Relatórios detalhados sobre diferentes aspectos do desempenho da equipe, análise de jogos e outros insights relevantes.

[x] **Watchlists**: Listas de observação de jogadores ou equipes, para monitoramento de desempenho e possíveis transferências futuras.

## Pré-requisitos

- Token de acesso à API Scoustastic: necessário para autenticação e acesso aos dados.
- Conhecimento dos ativos de dados específicos que pretende recuperar: entendimento das entidades e dados disponíveis na API Scoutastic.

## Requisitos

- Python 3.x: Versão compatível para execução do conector.- Biblioteca do Snowflake
- Biblioteca Requests: Para realizar requisições HTTP à API Scoutastic.

## Configuração

### Variaveis de Ambiente

As seguintes variáveis de ambiente são requeridas para execução do step:

- `SCOUTASTIC_TOKEN`: token de autenticação para acessar a API Scoutastic.
- `TEAM_IDENTIFIER`: Identificador do time para acessar a API (exemplo: "galo").

## Uso

### Arquivo de Configuração (config.json)

- No caso de execução fora do Orchest, é necessário fornecer um arquivo de configuração JSON contendo os parâmetros de entrada. O formato esperado é:

```json
{
  "auth_token": "Bearer <seu_token_aqui>",
  "team_identifier": "galo",
  "player_ids": "PLAYER_ID_1,PLAYER_ID_2,PLAYER_ID_3"
}
```

### Variáveis de Passagem no Orchest

- Se estiver utilizando o Orchest, passe os parâmetros como `team_identifier` e `player_ids` (este parametro vária de acordo com o step, neste caso, `players_ids` é usado para pegar dados do endpoint players/{player_id}) via interface de usuário do Orchest.
  - player_ids deve ser uma lista separada por vírgulas de IDs dos jogadores que você deseja consultar.

## Execução

### Localmente (executando o script diretamente)

- Utilize o comando:

```bash
    python players_missed.py '{"auth_token": "Bearer <seu_token_aqui>",
    "team_identifier": "galo", "player_ids": "PLAYER1,PLAYER2,PLAYER3"}'
```

O script irá coletar dados e salvar no arquivo players_missed_data.json.

### No orchest

1. Configure os parâmetros SCOUTASTIC_TOKEN, team_identifier e player_ids na interface do Orchest.
2. Execute o step no Orchest, que coletará dados para o endpoint escolhido.

## Saída

- O conector salva os dados extraídos em arquivos JSON com a estrutura correspondente às entidades consultadas. Por exemplo, o arquivo players_missed_data.json contém os dados dos jogadores ausentes.