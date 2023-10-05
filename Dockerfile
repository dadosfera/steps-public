FROM python:3.8

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION

# Define o diretório de trabalho como /app
WORKDIR /project-dir

# Copia o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install -y tesseract-ocr tesseract-ocr-por poppler-utils gettext
RUN install pyOpenSSL --upgrade
# Install any dependencies you have in this shell script,
# see https://docs.orchest.io/en/latest/fundamentals/environments.html#install-packages

# E.g. mamba install -y tensorflow

# Copia todo o conteúdo do diretório atual para /app no contêiner
COPY ./steps /project-dir/steps

RUN aws codeartifact login --tool pip --domain dadosfera --domain-owner 611330257153 --region us-east-1 --repository dadosfera-pip
RUN pip3 install dadosfera==1.3.0b6 dadosfera_logs==1.0.3
