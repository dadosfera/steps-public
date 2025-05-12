import orchest
import logging
import os
import requests
import pandas as pd
import time
import re
import json
import sys
import math
from datetime import datetime, timezone
import boto3
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get data from param
endpoint = orchest.get_step_param('endpoint')

# Set Last Update Date JSON File
LAST_UPDATE_PATH = f"state/last_update_{endpoint}.json"

# Set URL
url = f"https://sponte-bi.sponteweb.com.br/api/v1/extracoes/{endpoint}"

# Cálculo da quantidade máxima de requisições por step
with open("main.orchest", "r", encoding="utf-8") as file:
    json_data = json.load(file)
    
# Count occurrences of "get_sponte_data.py"
count_of_steps = sum(1 for step in json_data["steps"].values() if step.get("file_path") == "get_sponte_data.py")

# Cálculo para o Máximo de requesições da API
MAX_REQ_PER_MINUTE = 1000/count_of_steps
MAX_REQ_PER_MINUTE = math.floor(MAX_REQ_PER_MINUTE)

class SponteAPI:
    def __init__(
        self,
        logger: logging.Logger,
        api_key: str
    ):
        self.logger = logger
        self.api_key = api_key


    # Load schema from JSON file
    def load_schema_from_file(self, entity_name, schema_file="schemas/schemas.json"):
        with open(schema_file, "r") as f:
            schemas = json.load(f)

        if entity_name not in schemas:
            raise ValueError(f"Schema for entity '{entity_name}' not found in file.")

        # Convert JSON structure to PyArrow schema
        fields = []
        type_mapping = {
            "int64": pa.int64(),
            "int8": pa.int8(),
            "float64": pa.float64(),
            "string": pa.string(),
            "timestamp[ns]": pa.timestamp("ns", tz=None)
        }

        for column, dtype in schemas[entity_name].items():
            if dtype not in type_mapping:
                raise ValueError(f"Unsupported type '{dtype}' in schema for '{column}'.")
            fields.append((column, type_mapping[dtype]))

        return pa.schema(fields)
        
    def get_last_update(self):
        """
        Lê o 'last_update' de um arquivo JSON (LAST_UPDATE_PATH).
        Retorna None se não existir ou se houver falha.
        Exemplo: {"last_update": "2024-12-27T10:46:28Z"}
        """
        if not os.path.exists(LAST_UPDATE_PATH):
            self.logger.info(f"[get_last_update] Arquivo {LAST_UPDATE_PATH} não encontrado. Retornando None.")     
            return None

        try:
            with open(LAST_UPDATE_PATH, "r") as f:
                data = json.load(f)
                last_update = data.get("last_update")
                self.logger.info(f"[get_last_update] last_update carregado: {last_update}")
                return last_update
        except Exception as e:
            self.logger.error(f"[get_last_update] Erro ao carregar o arquivo {LAST_UPDATE_PATH}: {e}")
            return None

    def save_last_update(self, timestamp_str):
        """
        Salva o timestamp (ex.: '2024-01-01T00:00:00Z') em arquivo JSON.
        """
        try:
            with open(LAST_UPDATE_PATH, "w") as f:
                json.dump({"last_update": timestamp_str}, f)
            self.logger.info(f"[save_last_update] Valor '{timestamp_str}' salvo com sucesso em {LAST_UPDATE_PATH}.")
        except Exception as e:
            self.logger.error(f"[save_last_update] Erro ao salvar no arquivo {LAST_UPDATE_PATH}: {e}")
            raise

    def find_max_updated_at(self, data):
        """
        Percorre a lista dos dados e identifica o maior valor de 'DataExtracao'.
        Retorna o timestamp no formato 'YYYY-MM-DDTHH:MM:SSZ'.
        """
        max_dt = None

        formats = [
            "%Y-%m-%dT%H%M%S.%f",  
            "%Y-%m-%d %H:%M:%S",    
            "%d/%m/%Y %H:%M",       
            "%Y-%m-%d",
            "%Y-%m-%dT%H%M%S"
        ]
        
        for d in data:
            attributes = d.get("DataExtracao")
            def parse_datetime(attributes):
                for fmt in formats:
                    try:
                        return datetime.strptime(attributes, fmt)
                    except ValueError:
                        continue  # Try the next format

                raise ValueError(f"Date format not recognized: {attributes}")

            dt = parse_datetime(attributes)
            # Format to the desired format
            formatted_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            if formatted_date:
                try:
                    dt = datetime.fromisoformat(formatted_date.replace("Z", "+00:00"))
                    dt_utc = dt.astimezone(timezone.utc)
                    if not max_dt or dt > max_dt:
                        max_dt = dt_utc
                except ValueError:
                    # Caso o formato não seja compatível, ignora e segue
                    self.logger.info(f"[find_max_updated_at] Formato inválido: {formatted_date}")
                    pass
        if max_dt:
            formatted = max_dt.strftime("%Y-%m-%dT00:00:00Z")
            return formatted
        return None

    def fetch_data(self, cod_cli_sponte, data_extracao, api_key, count):
        """
        Faz a chamada à API.
        """

        headers = {'x-api-key': api_key}
        page_number = 1
        all_items = []

        while True:
            params = {
                'CodCliSponte': cod_cli_sponte,
                'DataExtracao': data_extracao,
                'PageNumber': page_number
            }
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()  # Verifica se houve erro HTTP
                data = response.json()
                status_code = response.status_code

                # Log da resposta do servidor
                self.logger.info(f"Response for CodCliSponte {cod_cli_sponte}: CurrentPage({data['currentPage']}), TotalPages({data['totalPages']}), StatusCode:{status_code})")
                all_items.extend(data['items'])

                count += 1

                # api wait MAX_REQ_PER_MINUTE
                if count == MAX_REQ_PER_MINUTE:
                    logger.info("[fetch_data] Limite de req/min atingido: aguardando 60 segundos...")
                    time.sleep(60)
                    count=0

                # Verifica se há mais páginas
                if not data.get('hasNext'):
                    break
                page_number += 1

            except requests.exceptions.HTTPError as err:
                self.logger.info(f'HTTP error occurred for CodCliSponte {cod_cli_sponte}: {err}')
                self.logger.info(f'Server response: {response.text}')
                break
            except Exception as e:
                self.logger.info(f'An error occurred for CodCliSponte {cod_cli_sponte}: {e}')
                break

        return all_items, count

    def clean_data(self, data):
        # Função para remover caracteres ilegais de strings
        illegal_chars = re.compile(r'[<>:"/\\|?*\x00-\x1F\x7F]')
        for item in data:
            for key in item.keys():
                if isinstance(item[key], str):
                    item[key] = illegal_chars.sub('', item[key])
        return data
    
    def process_and_send_df_to_next_step(self, data):
        outgoing_variable_name = orchest.get_step_param('outgoing_variable_name')
        
        df_sponte = pd.DataFrame(data)
        if df_sponte.empty:
            self.logger.info("Nenhum dado para processar.")
            return
        orchest.output(df_sponte, name=outgoing_variable_name)
        self.logger.info(f"[process_and_send_to_next_step] Dataframe exportado para variável '{outgoing_variable_name}' com sucesso.")
        
    def process_and_upload_to_s3(self, data, bucket_name, prefix):
        """Converts data to a DataFrame, splits by 'DataExtracao', and uploads each split file to S3."""
        client = boto3.client('s3', region_name='us-east-1')
        df = pd.DataFrame(data)
        schema = self.load_schema_from_file(entity_name=endpoint)

        for field in schema:
            col_name = field.name
            col_type = field.type

            if col_name in df.columns:
                if pa.types.is_integer(col_type):
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                elif pa.types.is_floating(col_type):
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype(float)
                elif pa.types.is_boolean(col_type):
                    df[col_name] = df[col_name].astype(bool)
                elif pa.types.is_timestamp(col_type):
                    df[col_name] = pd.to_datetime(df[col_name], errors='coerce').astype('datetime64[ns]')
                else:
                    df[col_name] = df[col_name].astype('string')  

                

        df['DataExtracao'] = pd.to_datetime(df['DataExtracao'], errors='coerce').astype('datetime64[ns]')

        for date, group in df.groupby(df['DataExtracao'].dt.date):
            file_name = f"{endpoint}_{date}.parquet"
            s3_output_path = f"{prefix}/{file_name}"

            buffer = BytesIO()
            
            schema = self.load_schema_from_file(entity_name=endpoint)
            
            table = pa.Table.from_pandas(group, schema=schema, preserve_index=False)

            pq.write_table(table, buffer)

            buffer.seek(0)
            
            client.upload_fileobj(buffer, bucket_name, s3_output_path)


            self.logger.info(f"Uploaded split file to s3://{bucket_name}/{s3_output_path}")
            
    def run(self, sponte_code_list, data_extracao, api_key, is_historical:bool=False):
        """
        Fluxo principal
        """
        bucket_name = orchest.get_step_param('bucket_name')
        prefix = orchest.get_step_param('prefix')
        
        output_type = orchest.get_step_param('output_type')
        
        if prefix is None:
                prefix = ''
        
        all_data = []
        count = 0

        try:
            # Get last param date
            last_update = self.get_last_update()
            
            if last_update and not is_historical:
                dt = datetime.strptime(last_update, "%Y-%m-%dT%H:%M:%SZ")
                # Format to date only
                data_extracao = dt.strftime("%Y-%m-%d")

                self.logger.info(f"[run] INCREMENTAL a partir de updated_at={data_extracao}")
                
            else:
                self.logger.info(f"[run] FULL LOAD - Buscando dados a partir do dia {data_extracao}")
            # Chamada da API de todas as filiais
            for cod_cli in sponte_code_list:
                self.logger.info(f'[run] Fetching data for CodCliSponte: {cod_cli}')
                data, count = self.fetch_data(cod_cli, data_extracao, api_key, count)
                all_data.extend(data)
            self.logger.info(f'[run] Total de registros coletados: {len(all_data)}')

            # Limpa os dados
            if all_data:
                cleaned_data = self.clean_data(all_data)
                self.logger.info(f"[run] Todos os dados limpos.")
            else:
                cleaned_data = all_data
                self.logger.info(f"[run] Nenhum dado para limpeza.")

            if cleaned_data:
                
                if output_type == "send_dataframe_to_next_step":
                    self.process_and_send_df_to_next_step(cleaned_data)
                    self.logger.info("[run] Dataframe enviado para o próximo step")
                elif output_type == "upload_to_s3":
                    self.process_and_upload_to_s3(cleaned_data, bucket_name, prefix)
                    self.logger.info("[run] Dados transformados em parquet e fazendo upload para o S3")
                else:
                    self.logger.info("[run] Nenhum 'updated_at' válido encontrado; nada a salvar.")
                
                new_last_update = self.find_max_updated_at(cleaned_data)
                self.logger.info(f"[run] Valor encontrado: {new_last_update}")

                if new_last_update:
                    self.save_last_update(new_last_update)
                    self.logger.info(f"[run] Arquivo '{LAST_UPDATE_PATH}' atualizado.")
                else:
                    self.logger.info("[run] Nenhum 'DataExtracao' válido encontrado; nada a salvar.")
            else:
                self.logger.info("[run] Nenhum dado retornado. Finalizando o Step")

        except Exception as e:
            self.logger.info(f"Ocorreu um erro: {e}")
            raise
        
def orchest_handler():
    api_key = os.getenv('x-api-key')
    input_type = orchest.get_step_param('input_type')

    if input_type == "from_step_param":
        data_extracao = orchest.get_step_param('data_extracao')
        cod_cli_sponte = orchest.get_step_param('cod_cli_sponte')
        is_historical = orchest.get_step_param('is_historical_load')
        sponte_code_list = [cod_cli_sponte]

    elif input_type == "from_incoming_variable":
        data_extracao = orchest.get_step_param('data_extracao')
        incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        is_historical = orchest.get_step_param('is_historical_load')
        # Get data from incoming steps.
        input_data = orchest.get_inputs()
        sponte_code_list = input_data[f"{incoming_variable_name}"]
        
    
    handler = SponteAPI(
        logger=logger,
        api_key=api_key
    )
    handler.run(sponte_code_list, data_extracao, api_key, is_historical=is_historical)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    api_key = config.get("api_key")

    if not api_key:
        raise ValueError(
            "'api_key' must be provided in the configuration.")

    handler = SponteAPI(
        api_key=api_key
    )
    handler.run(sponte_code_list, data_extracao, api_key)

if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()