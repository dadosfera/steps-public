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
