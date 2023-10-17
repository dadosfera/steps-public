# Documentação de Recuperação de Ativos de Dados

[Maestro](https://maestro.dadosfera.ai) é uma plataforma API dedicada a oferecer soluções eficientes para a gestão de dados. O esquema fornecido possibilita a recuperação de ativos de dados através de sua API, especificando determinados parâmetros.


## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)

## Sobre o projeto

O esquema fornecido descreve a estrutura do payload JSON destinado à recuperação de ativos de dados específicos no Maestro. Os usuários podem especificar parâmetros para definir quais ativos de dados desejam acessar, garantindo precisão e eficiência na extração de dados.

## Pré-requisitos

- Acesso à API do Maestro.
- Conhecimento dos ativos de dados específicos que pretende recuperar.

## Configuração

### Variáveis de Ambiente

As seguintes variáveis de ambiente são requeridas para execução do step:

- `DADOSFERA_USERNAME`
- `DADOSFERA_PASSWORD`

### Parâmetros:

- **maestro_base_url**: Representa a URL base para a API do Maestro. Valores aceitáveis são "https://maestro.dadosfera.ai" e "https://maestro.stg.dadosfera.ai".

- **output_variable_name**: Especifica o nome da variável onde os dados resultantes serão armazenados.

- **additional_params**: Um array contendo parâmetros que atuam como filtros para determinar quais ativos de dados serão recuperados. Cada parâmetro é definido por uma `chave` (nome do filtro) e um `valor` (critério do filtro).

_Observação_: É essencial definir a URL base correta e especificar a variável de saída com cuidado para garantir que os dados sejam extraídos com precisão.


#### Exemplos de configuração

## Getting All Data Assets of a specific Pipeline

```json
{
  "maestro_base_url": "https://maestro.dadosfera.ai",
  "output_variable_name": "arbitrary_output_name",
  "additional_params": [
    {
      "key": "pipeline_id",
      "value": "28f8de4d-f46d-47a4-83fb-42069c1861ae"
    }
  ]
}
```


## Getting All Dashboards

```json
{
  "maestro_base_url": "https://maestro.dadosfera.ai",
  "output_variable_name": "arbitrary_output_name",
  "additional_params": [
    {
      "key": "data_asset_type",
      "value": "dashboard"
    }
  ]
}
```