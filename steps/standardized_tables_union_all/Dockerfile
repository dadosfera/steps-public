FROM python:3.8-slim

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}

ARG SECRET_ID

WORKDIR /project-dir

COPY requirements.txt .

RUN pip install -r requirements.txt && \
    aws codeartifact login --tool pip --domain dadosfera --domain-owner 611330257153 --region us-east-1 --repository dadosfera-pip && \
    pip3 install dadosfera==1.3.0b6 dadosfera_logs==1.0.3

COPY . .

CMD python3 standardized_tables_union_all.py "{\"secret_id\": \"${SECRET_ID}\"}"