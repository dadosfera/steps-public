# Documentação para o Step Trigger Job

 O step `trigger_job.py` permite acionar um job específico (aqui chamado de Target Job), com base na execução de outra pipeline. Normalmente esse step estará no final da pipeline. Vale observar que esse step funciona tanto para acionarmos jobs no mesmo projeto dentro do módulo de inteligência, quanto para jobs em projetos diferentes.


## Sumário

- [Documentação para o Step Trigger Job](#documentação-para-o-step-trigger-job)
  - [Sumário](#sumário)
  - [Sobre o step](#sobre-o-step)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração](#configuração)
    - [Variáveis de Ambiente](#variáveis-de-ambiente)
    - [Parâmetros](#parâmetros)
  - [Exemplo de execução do job](#exemplo-de-execução-do-job)

## Sobre o step

O código Python fornecido, `trigger_job.py`, define a classe `TriggerJob` para fazer o trigger de um job específico.

## Pré-requisitos

- Acesso às variáveis de ambiente `ORCHEST_USER` e `ORCHEST_PASSWORD`.
- Conhecimento do `instance_url`, `target_pipeline_uuid` e `target_job_name` do job que deseja acionar.

## Configuração

### Variáveis de Ambiente

As seguintes variáveis de ambiente são necessárias para a execução do step:

- `ORCHEST_USER`: Nome de usuário para autenticação no Orchest.
- `ORCHEST_PASSWORD`: Senha para autenticação no Orchest.

### Parâmetros

Esses parâmetros deverão ser editados no arquivo json `trigger_job.py.schema.json`.

- **instance_url**: URL base para o módulo de inteligência. Normalmente estão nesse formato: `https://app-intelligence-CLIENTE.dadosfera.ai`
  
- **target_pipeline_uuid**: ID da pipeline onde o job que deseja acionar está localizado.
  
- **target_job_name**: Nome do job que deseja acionar. É importante manter o mesmo nome sempre que recriar o job.


Ainda, quando executar esse step fora do módulo de inteligência é possível ter os mesmos resultados, porém deve ser utilizado um arquivo de configuração .json, conforme o exemplo abaixo:

```json
{
  "instance_url": "https://app-intelligence-CLIENTE.dadosfera.ai",
  "target_pipeline_uuid": "pipeline_uuid_a",
  "target_job_name": "nome_do_job_01"
}
```

Este exemplo aciona o job com o nome "nome_do_job_01" na pipeline com o ID "pipeline_uuid_a".


## Exemplo de execução do job

Dentro do módulo de inteligência do cliente fictício "Best Company" há dois projetos, o primeiro chamado "etl" e o segundo chamado "modelagem", cada um contando com uma pipeline e um job apenas. O job da pipeline "etl" se chama `etl-main` e da "modelagem" se chama `modelagem-main`.

A partir disso, queremos acionar o job `modelagem-main`, logo após a execução do `etl-main`. Para isso, executamos os seguintes passos:

1) Adicionamos o script `trigger_job.py` como último step da pipeline do etl:

   ```
   pipeline etl

   [Step 1] -> [Step 2] -> [Step 3] -> [Trigger Modelagem]
   ```

   O Trigger Modelagem será o script `trigger_job.py`.

2) Editamos o arquivo de configuração `trigger_job.py.schema.json`. 
   
   2.1. instance_url como `https://app-intelligence-best-company.dadosfera.ai`

   2.2. target_pipeline_uuid como o id da pipeline que está o job `modelagem-main`. Esse id pode ser obtido dentro do módulo, em "Pipelines" e checando a url, selecionando o valor após "pipeline_uuid=".

   2.3. target_job_name como `modelagem-main`

3) Agora no step em si, em "Parameters" selecionamos os valores corretos adicionados. Após, rodamos o step, e o job da `modelagem-main` será acionado quando executarmos o step `Trigger Modelagem`







