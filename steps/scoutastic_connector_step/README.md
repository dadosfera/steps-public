# Scoutastic Connector Step

Este STEP connector é dedicado à API Scoutastic, que permite extrair dados de várias rotas da API, alterando apenas parâmetros, funções de paginação e o destino dos dados.

## Entidades

O conector suporta a extração de dados das seguintes entidades:

### Appointments

Detalhes sobre compromissos e eventos, como agendamentos de partidas, treinamentos e reuniões.

### Competitions

Informações sobre competições, incluindo dados como nome da competição, temporada, equipes participantes e estatísticas relevantes.

### Managers

Dados sobre gestores e técnicos, incluindo informações pessoais, histórico de gestão e estatísticas de desempenho.

### Matches

Detalhes sobre partidas, incluindo data, hora, local, equipes envolvidas, resultados e estatísticas do jogo.

### Players

Informações sobre jogadores, incluindo dados pessoais, histórico de carreira, estatísticas de desempenho e status atual.

### Players Missed

Listas de jogadores ausentes em determinados eventos ou partidas, incluindo razões de ausência.

### Transfers History

Histórico de transferências de jogadores entre clubes, incluindo detalhes como data da transferência, valores envolvidos, clubes de origem e destino.

### Teams

Informações sobre as equipes, incluindo composição do elenco, treinadores, desempenho histórico e estatísticas atuais.

### Reports

Relatórios detalhados sobre diferentes aspectos do desempenho da equipe, análise de jogos e outros insights relevantes.

### Watchlists

Listas de observação de jogadores ou equipes, para monitoramento de desempenho e possíveis transferências futuras.

## Pré-requisitos

- Token de acesso à API Scoustastic: necessário para autenticação e acesso aos dados.
- Conhecimento dos ativos de dados específicos que pretende recuperar: entendimento das entidades e dados disponíveis na API Scoutastic.

## Requisitos

- Python 3.x: Versão compatível para execução do conector.- Biblioteca do Snowflake
- Biblioteca Pandas: Para manipulação e análise de dados.
- Biblioteca Requests: Para realizar requisições HTTP à API Scoutastic.

## Configuração

### Variaveis de Ambiente

As seguintes variáveis de ambiente são requeridas para execução do step:

- `SCOUTASTIC_TOKEN`: token de autenticação para acessar a API Scoutastic.

## Uso

## Saída
