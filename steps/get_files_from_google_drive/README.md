# Documentação para o Step Google Drive List Files

O script `google_drive_list_files.py` permite acessar e extrair todos os arquivos em uma pasta específica do Google Drive, autenticando-se com um serviço de conta de serviço (service account).

## Sumário

- [Documentação para o Step Google Drive List Files](#documentação-para-o-step-google-drive-list-files)
  - [Sumário](#sumário)
  - [Sobre o script](#sobre-o-script)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração](#configuração)
    - [Parâmetros](#parâmetros)
    - [Para executar como um script](#para-executar-como-um-script)

## Sobre o script

O script Python fornecido, `google_drive_list_files.py`, define funções para autenticar-se no Google Drive e listar todos os arquivos em uma pasta especificada.

## Pré-requisitos

- Acesso ao serviço de conta de serviço (service account) do Google Drive.
- Conhecimento do ID da pasta no Google Drive que deseja listar.

## Configuração


### Parâmetros

Os seguintes parâmetros deverão ser fornecidos ao executar o script:

- **service_account_file**: Caminho para o arquivo JSON de credenciais da conta de serviço do Google Drive.
  
- **selected_folder_id**: ID da pasta no Google Drive da qual deseja listar os arquivos.
  
- **outgoing_variable_name**: Nome da variável de saída a ser utilizada para armazenar a lista de arquivos. 

Obs: Esse step `google_drive_list_files` é facilmente integrável com outros steps, e assim sendo, a variável **outgoing_variable_name** deverá ter o mesmo nome da variável **input_variable_name** do step posterior. 

EX: Executando o step `put_objects_in_s3` logo após o `google_drive_list_files` estamos lendo os arquivos do Google Drive e adicionando no S3. 

### Para executar como um script

Quando executar esse step fora do módulo de inteligência é possível ter os mesmos resultados, porém deve ser utilizado um arquivo de configuração .json, conforme o exemplo abaixo:

```json
{
  "service_account_file": "/caminho/para/seu/arquivo_de_credenciais.json",
  "selected_folder_id": "ID_da_sua_pasta_no_Google_Drive",
  "outgoing_variable_name": "nome_da_variável_de_saída"
}
```
