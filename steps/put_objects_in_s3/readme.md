# Descrição do Código

Este script processa arquivos locais e os envia para um bucket S3.  
Ele pode ser executado de duas formas:
1. Como um passo dentro de um pipeline do **Orchest**.
2. Como um **script independente**.

### Recursos
- ✅ Leitura de PDFs (binário) e arquivos de texto.
- ✅ Upload para o S3 usando **boto3**.
- ✅ Execução como **script ou pipeline**.
- ✅ Logs detalhados para **monitoramento**.

## Configuração (schema.json e uischema.json)
Para executar esse step é necessário buildar o Environment a seguir:  
```
aws codeartifact login --tool pip --domain dadosfera --domain-owner 611330257153 --region us-east-1 --repository dadosfera-pip
pip3 install dadosfera==1.16.0 dadosfera_logs==1.0.3
# Instalar pacotes de manipulação de PDFs
pip install PyPDF2
# Atualizar pacotes essenciais para requisições
pip install --upgrade requests urllib3 charset_normalizer
# Instalar pacotes adicionais para OCR e manipulação de imagens
pip install --upgrade pytesseract pymupdf pillow boto3
# Instalar LangChain e pacotes relacionados
pip install --upgrade langchain langchain-community langchain-openai
pip install --upgrade "deeplake[enterprise]"
# Reforçar a instalação do pacote OpenAI, caso não esteja instalado
pip install --upgrade openai
```

### Parâmetros Main Configuration:
- **Bucket Name**: Nome do S3 localizado dentro da INFRA (ex: dadosfera-landing-dadosferademo-prd-us-east-1-611330257153)

- **Prefix**: Localização do path que salvará os arquivos.

- **Input Type**: `from_incoming_variable` para usar dados processado na pipeline ou `from_filepath` para buscar os dados no código fonte

### Parâmetros Input Configuration:
Se Input Type selecionado foi `from_filepath` deve ser passado o path de todos os arquivos no código fonte que será salvo no S3.