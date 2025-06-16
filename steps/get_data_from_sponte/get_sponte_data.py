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
import traceback
from datetime import datetime, timezone, timedelta, date

import boto3
from io import BytesIO
from dadosfera.services.snowflake import get_snowpark_session, get_snowflake_connector_session

import pyarrow as pa
import pyarrow.parquet as pq


# Global error handler to catch and log all exceptions
def safe_execute(func):
    """Decorator to safely execute functions and catch all exceptions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    return wrapper


ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Get data from param
try:
    endpoint = orchest.get_step_param('endpoint')
except Exception as e:
    endpoint = 'fatoalunosativos'

# Set Last Update Date JSON File
LAST_UPDATE_PATH = f"state/last_update_{endpoint}.json"

# Set URL
url = f"https://sponte-bi.sponteweb.com.br/api/v1/extracoes/{endpoint}"


# Cálculo da quantidade máxima de requisições por step
try:
    with open("main.orchest", "r", encoding="utf-8") as file:
        json_data = json.load(file)
    
    # Count occurrences of "get_sponte_data.py"
    count_of_steps = sum(1 for step in json_data["steps"].values() if step.get("file_path") == "get_sponte_data.py")
    
    # Cálculo para o Máximo de requesições da API
    MAX_REQ_PER_MINUTE = 1000/count_of_steps
    MAX_REQ_PER_MINUTE = math.floor(MAX_REQ_PER_MINUTE)
except Exception as e:
    logger.warning(f"Error loading main.orchest file: {str(e)}. Using default MAX_REQ_PER_MINUTE=100")
    MAX_REQ_PER_MINUTE = 100


class SponteAPI:
    def __init__(
        self,
        logger: logging.Logger = None,
        api_key: str = None,
        secret_id: str = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.api_key = api_key
        self.secret_id = secret_id

    # Load schema from JSON file
    def load_schema_from_file(self, entity_name, schema_file="schemas/schemas.json"):
        try:
            if not os.path.exists(schema_file):
                self.logger.warning(f"Schema file {schema_file} not found. Using empty schema.")
                return pa.schema([])
                
            with open(schema_file, "r") as f:
                schemas = json.load(f)

            if entity_name not in schemas:
                self.logger.warning(f"Schema for entity '{entity_name}' not found in file. Using empty schema.")
                return pa.schema([])

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
                    self.logger.warning(f"Unsupported type '{dtype}' in schema for '{column}'. Using string type instead.")
                    fields.append((column, pa.string()))
                else:
                    fields.append((column, type_mapping[dtype]))

            return pa.schema(fields)
        except Exception as e:
            self.logger.error(f"Error loading schema file: {str(e)}. Using empty schema.")
            return pa.schema([])

    def get_last_update(self):
        """
        Lê o 'last_update' de um arquivo JSON (LAST_UPDATE_PATH).
        Retorna None se não existir ou se houver falha.
        Exemplo: {"last_update": "2024-12-27T10:46:28Z"}
        """
        try:
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
        except Exception as e:
            self.logger.error(f"[get_last_update] Erro inesperado: {str(e)}")
            return None

    def save_last_update(self, timestamp_str):
        """
        Salva o timestamp (ex.: '2024-01-01T00:00:00Z') em arquivo JSON.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(LAST_UPDATE_PATH), exist_ok=True)
            
            with open(LAST_UPDATE_PATH, "w") as f:
                json.dump({"last_update": timestamp_str}, f)
            self.logger.info(f"[save_last_update] Valor '{timestamp_str}' salvo com sucesso em {LAST_UPDATE_PATH}.")
        except Exception as e:
            self.logger.error(f"[save_last_update] Erro ao salvar no arquivo {LAST_UPDATE_PATH}: {e}")
            # Don't raise the exception, just log it

    def fetch_data_with_retry(self, url, headers, params, max_retries=3):
        """
        Faz a validação no retorno da requisição feita na API com múltiplas tentativas.
        """
        try:
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=60)
                    
                    if response.status_code == 200:
                        self.logger.info(f"Requisição bem-sucedida na tentativa {attempt}.")
                        return response.json(), 200

                    elif response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 90
                        self.logger.warning(f"429 - Aguardando {wait_time}s antes de tentar novamente (tentativa {attempt}/{max_retries}).")
                        time.sleep(wait_time)
                        continue  # Try again after waiting

                    elif response.status_code == 500:
                        self.logger.error(f"500 - Erro interno no servidor (tentativa {attempt}/{max_retries}).")
                        if attempt < max_retries:
                            time.sleep(30)  # Wait before retrying on server error
                            continue
                        return [], 500

                    else:
                        logger.error(f"Erro inesperado {response.status_code}: {response.text} (tentativa {attempt}/{max_retries}).")
                        if attempt < max_retries:
                            time.sleep(15)  # Wait before retrying on other errors
                            continue
                        return [], response.status_code
                
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Erro na requisição (tentativa {attempt}/{max_retries}): {str(e)}")
                    if attempt < max_retries:
                        time.sleep(15)
                        continue
                    return [], 0  # Return 0 as status code for connection errors
            
            # If we've exhausted all retries
            self.logger.error(f"Todas as {max_retries} tentativas falharam.")
            return [], 0
        
        except Exception as e:
            self.logger.error(f"Erro inesperado em fetch_data_with_retry: {str(e)}")
            return [], 0

    def find_max_updated_at(self, data):
        """
        Percorre a lista dos dados e identifica o maior valor de 'DataExtracao'.
        Retorna o timestamp no formato 'YYYY-MM-DDTHH:MM:SSZ'.
        """
        try:
            if not data:
                self.logger.warning("[find_max_updated_at] Lista de dados vazia.")
                return None
                
            max_dt = None

            formats = [
                "%Y-%m-%dT%H%M%S.%f",  
                "%Y-%m-%d %H:%M:%S",    
                "%d/%m/%Y %H:%M",       
                "%Y-%m-%d",
                "%Y-%m-%dT%H%M%S"
            ]
            
            for d in data:
                try:
                    attributes = d.get("DataExtracao")
                    if not attributes:
                        continue
                        
                    def parse_datetime(attributes):
                        for fmt in formats:
                            try:
                                return datetime.strptime(attributes, fmt)
                            except ValueError:
                                continue  # Try the next format
                        
                        self.logger.warning(f"[find_max_updated_at] Date format not recognized: {attributes}")
                        return None

                    dt = parse_datetime(attributes)
                    if not dt:
                        continue
                        
                    # Format to the desired format
                    try:
                        formatted_date = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        dt_utc = dt.replace(tzinfo=timezone.utc)
                        if not max_dt or dt_utc > max_dt:
                            max_dt = dt_utc
                    except Exception as e:
                        self.logger.warning(f"[find_max_updated_at] Erro ao formatar data: {str(e)}")
                except Exception as e:
                    self.logger.warning(f"[find_max_updated_at] Erro ao processar item: {str(e)}")
                    continue
                    
            if max_dt:
                try:
                    formatted = max_dt.strftime("%Y-%m-%dT00:00:00Z")
                    return formatted
                except Exception as e:
                    self.logger.error(f"[find_max_updated_at] Erro ao formatar data máxima: {str(e)}")
            
            return None
        except Exception as e:
            self.logger.error(f"[find_max_updated_at] Erro inesperado: {str(e)}")
            return None
    
    def insert_error_date(self, data_extracao, status_code, table_name, secret_id, cod_cli_sponte=None):
       try:
            if not cod_cli_sponte:
                self.logger.warning(f"[insert_error_date] cod_cli_sponte não fornecido, usando valor padrão 0")
                cod_cli_sponte = 0
                
            session = get_snowflake_connector_session(secret_id)
            try:

                query = f'''INSERT INTO DADOSFERA_PRD_CCAACOMBR.STAGING.MONITORING_SPONTE (ENDPOINT,DATE_EXTRACAO,DATA_EXECUTE,STATUS_CODE_EXECUTE,COD_CLI_SPONTE) VALUES ('{table_name}','{data_extracao}','{datetime.now()}',{status_code},{cod_cli_sponte}) '''
                
                session.execute(query)
                logger.info(f"[insert_error_date] Inserção da data:{data_extracao} na tabela:{table_name} com erro na coleta")
                return True
            except Exception as e:
                logger.error(f"[insert_error_date] Erro ao executar query: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"[insert_error_date] Erro ao conectar com Snowflake: {str(e)}")
            return False

    def fetch_data(self, cod_cli_sponte, data_extracao, api_key, count, secret_id):
        """
        Faz a chamada à API.
        """
        headers = {'x-api-key': api_key}
        page_number = 1
        all_items = []
        req_start_time = time.time()
        max_pages = 1000  # Safety limit to prevent infinite loops
        try:
            while page_number <= max_pages:
                page_number += 1
                params = {
                    'CodCliSponte': cod_cli_sponte,
                    'DataExtracao': data_extracao,
                    'PageNumber': page_number
                }

                data, status_code = self.fetch_data_with_retry(url, headers, params)

                if status_code == 200 and isinstance(data, dict):
                    current_page = data.get('currentPage', page_number)
                    total_pages = data.get('totalPages', 'N/A')
                    self.logger.info(f"Response para CodCliSponte {cod_cli_sponte}: Página {current_page}/{total_pages}")

                    items = data.get('items', [])
                    if isinstance(items, list):
                        all_items.extend(items)
                    else:
                        self.logger.warning(f"'items' não é uma lista válida: {type(items)}")

                    count += 1

                    # Limite de requisições por minuto
                    if count >= MAX_REQ_PER_MINUTE:
                        elapsed = time.time() - req_start_time
                        if elapsed < 60:
                            wait_time = 60 - elapsed
                            self.logger.info(f"Limite de {MAX_REQ_PER_MINUTE} req/min atingido. Aguardando {int(wait_time)} segundos...")
                            time.sleep(wait_time)
                        req_start_time = time.time()
                        count = 0

                    if not data.get('hasNext', False):
                        break

                    page_number += 1

                else:
                    self.logger.warning(f"Falha na requisição. Status {status_code} para CodCliSponte {cod_cli_sponte}, DataExtracao {data_extracao}")
                    try:
                        self.insert_error_date(data_extracao, status_code, endpoint, secret_id, cod_cli_sponte)
                    except Exception as e:
                        self.logger.error(f"Erro ao registrar falha: {str(e)}")
                    break  

            return all_items, count

        except requests.exceptions.HTTPError as err:
            self.logger.error(f"Erro HTTP para CodCliSponte {cod_cli_sponte}: {err}")
            try:
                self.insert_error_date(data_extracao, 0, endpoint, secret_id, cod_cli_sponte)
            except Exception as e:
                self.logger.error(f"Erro ao registrar erro HTTP: {str(e)}")

        except Exception as e:
            self.logger.error(f"Erro inesperado em fetch_data para CodCliSponte {cod_cli_sponte}: {e}")
            self.logger.error(traceback.format_exc())
            try:
                self.insert_error_date(data_extracao, 0, endpoint, secret_id, cod_cli_sponte)
            except Exception as err:
                self.logger.error(f"Erro ao registrar erro inesperado: {str(err)}")

        return all_items, count

    def clean_data(self, data):
        """
        Função para remover caracteres ilegais de strings
        """
        try:
            if not data:
                return []
                
            illegal_chars = re.compile(r'[<>:"/\\|?*\x00-\x1F\x7F]')
            cleaned_data = []
            
            for item in data:
                try:
                    cleaned_item = {}
                    for key, value in item.items():
                        if isinstance(value, str):
                            cleaned_item[key] = illegal_chars.sub('', value)
                        else:
                            cleaned_item[key] = value
                    cleaned_data.append(cleaned_item)
                except Exception as e:
                    self.logger.warning(f"Error cleaning item: {str(e)}. Skipping this item.")
                    continue
                    
            return cleaned_data
        except Exception as e:
            self.logger.error(f"Error in clean_data: {str(e)}")
            return data  # Return original data if cleaning fails
    
    def process_and_send_df_to_next_step(self, data):
        try:
            outgoing_variable_name = orchest.get_step_param('outgoing_variable_name')
            
            if not data:
                self.logger.info("Nenhum dado para processar.")
                # Send empty dataframe instead of returning
                orchest.output(pd.DataFrame(), name=outgoing_variable_name)
                self.logger.info(f"[process_and_send_to_next_step] Dataframe vazio exportado para variável '{outgoing_variable_name}'.")
                return
                
            try:
                df_sponte = pd.DataFrame(data)
                if df_sponte.empty:
                    self.logger.info("Dataframe vazio após conversão.")
                    orchest.output(df_sponte, name=outgoing_variable_name)
                    self.logger.info(f"[process_and_send_to_next_step] Dataframe vazio exportado para variável '{outgoing_variable_name}'.")
                    return
                    
                orchest.output(df_sponte, name=outgoing_variable_name)
                self.logger.info(f"[process_and_send_to_next_step] Dataframe exportado para variável '{outgoing_variable_name}' com sucesso.")
            except Exception as e:
                self.logger.error(f"Error creating or sending dataframe: {str(e)}")
                # Send empty dataframe as fallback
                orchest.output(pd.DataFrame(), name=outgoing_variable_name)
                self.logger.info(f"[process_and_send_to_next_step] Dataframe vazio exportado como fallback.")
        except Exception as e:
            self.logger.error(f"Error in process_and_send_df_to_next_step: {str(e)}")
            # Try to send empty dataframe as last resort
            try:
                orchest.output(pd.DataFrame(), name="output")
                self.logger.info("[process_and_send_to_next_step] Dataframe vazio exportado como último recurso.")
            except:
                self.logger.error("Failed to send even empty dataframe as fallback.")
        
    def process_and_upload_to_s3(self, data, bucket_name, prefix):
        """Converts data to a DataFrame, splits by 'DataExtracao', and uploads each split file to S3."""
        try:
            if not data:
                self.logger.info("No data to upload to S3.")
                return
                
            try:
                df = pd.DataFrame(data)
                if df.empty:
                    self.logger.info("Empty dataframe, nothing to upload to S3.")
                    return
                    
                try:
                    schema = self.load_schema_from_file(entity_name=endpoint)
                except Exception as e:
                    self.logger.error(f"Error loading schema: {str(e)}. Using empty schema.")
                    schema = pa.schema([])

                # Process columns based on schema
                try:
                    for field in schema:
                        col_name = field.name
                        col_type = field.type

                        if col_name in df.columns:
                            try:
                                if pa.types.is_integer(col_type):
                                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                                elif pa.types.is_floating(col_type):
                                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype(float)
                                elif pa.types.is_boolean(col_type):
                                    df[col_name] = df[col_name].astype(bool)
                                elif pa.types.is_timestamp(col_type):
                                    df[col_name] = pd.to_datetime(df[col_name], errors='coerce', infer_datetime_format=True).astype('datetime64[ns]')
                                else:
                                    df[col_name] = df[col_name].astype('string')
                            except Exception as e:
                                self.logger.warning(f"Error converting column {col_name}: {str(e)}. Using original data.")
                except Exception as e:
                    self.logger.error(f"Error processing columns: {str(e)}")

                # Process DataExtracao column
                try:
                    if 'DataExtracao' in df.columns:
                        df['DataExtracao'] = pd.to_datetime(df['DataExtracao'], errors='coerce').astype('datetime64[ns]')
                except Exception as e:
                    self.logger.error(f"Error processing DataExtracao column: {str(e)}")
                    # Create a default date column if needed
                    if 'DataExtracao' not in df.columns:
                        df['DataExtracao'] = pd.to_datetime('today').date()

                # Group by date and upload
                try:
                    # Handle case where DataExtracao might not be valid for groupby
                    if 'DataExtracao' in df.columns and not df['DataExtracao'].isna().all():
                        groups = df.groupby(df['DataExtracao'].dt.date)
                    else:
                        # If DataExtracao is not usable, create a single group with today's date
                        today = pd.to_datetime('today').date()
                        groups = [(today, df)]
                        
                    for date, group in groups:
                        try:
                            file_name = f"{endpoint}_{date}.parquet"
                            s3_output_path = f"{prefix}/{file_name}"

                            buffer = BytesIO()
                            
                            # Create table with schema
                            try:
                                table = pa.Table.from_pandas(group, schema=schema, preserve_index=False)
                            except Exception as e:
                                self.logger.warning(f"Error creating table with schema: {str(e)}. Trying without schema.")
                                table = pa.Table.from_pandas(group)
                            
                            # Write table to buffer
                            try:
                                pq.write_table(table, buffer)
                                buffer.seek(0)
                            except Exception as e:
                                self.logger.error(f"Error writing table to buffer: {str(e)}")
                                continue
                            
                            # Upload to S3
                            try:
                                session_b3 = boto3.Session()
                                client = session_b3.client('s3')
                                client.upload_fileobj(buffer, bucket_name, s3_output_path)
                                self.logger.info(f"Uploaded split file to s3://{bucket_name}/{s3_output_path}")
                            except Exception as e:
                                self.logger.error(f"Error uploading to S3: {str(e)}")
                        except Exception as e:
                            self.logger.error(f"Error processing group for date {date}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Error in groupby operation: {str(e)}")
                    # Fallback: try to upload entire dataframe as one file
                    try:
                        file_name = f"{endpoint}_fallback.parquet"
                        s3_output_path = f"{prefix}/{file_name}"
                        buffer = BytesIO()
                        table = pa.Table.from_pandas(df)
                        pq.write_table(table, buffer)
                        buffer.seek(0)
                        session_b3 = boto3.Session()
                        client = session_b3.client('s3')
                        client.upload_fileobj(buffer, bucket_name, s3_output_path)
                        self.logger.info(f"Uploaded fallback file to s3://{bucket_name}/{s3_output_path}")
                    except Exception as e2:
                        self.logger.error(f"Error uploading fallback file: {str(e2)}")
            except Exception as e:
                self.logger.error(f"Error creating DataFrame: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in process_and_upload_to_s3: {str(e)}")
            self.logger.error(traceback.format_exc())
            
    def run(self, sponte_code_list, list_data_extracao, api_key, secret_id):
        """
        Fluxo principal
        """
        try:
            # Get parameters with error handling
            try:
                bucket_name = orchest.get_step_param('bucket_name')
            except Exception as e:
                self.logger.error(f"Error getting bucket_name: {str(e)}")
                bucket_name = None
                
            try:
                prefix = orchest.get_step_param('prefix')
                if prefix is None:
                    prefix = ''
            except Exception as e:
                self.logger.error(f"Error getting prefix: {str(e)}")
                prefix = ''
                
            try:
                output_type = orchest.get_step_param('output_type')
            except Exception as e:
                self.logger.error(f"Error getting output_type: {str(e)}")
                output_type = None
            
            all_data = []
            count = 0

            # Validate inputs
            if not sponte_code_list:
                self.logger.warning("Empty sponte_code_list. Nothing to process.")
                return
                
            if not list_data_extracao:
                self.logger.warning("Empty list_data_extracao. Nothing to process.")
                return

            # Main processing loop
            for data_extracao in list_data_extracao:
                current_data = []
                for cod_cli in sponte_code_list:
                    try:
                        self.logger.info(f'[run] Fetching data for CodCliSponte: {cod_cli}')
                        data, count = self.fetch_data(cod_cli, data_extracao, api_key, count, secret_id)
                        if data:
                            current_data.extend(data)
                    except Exception as e:
                        self.logger.error(f"Error fetching data for CodCliSponte {cod_cli}: {str(e)}")
                        # Continue with next code
                
                # Process data for this extraction date
                if current_data:
                    all_data.extend(current_data)
                    self.logger.info(f'[run] Total de registros coletados para {data_extracao}: {len(current_data)}')
                else:
                    self.logger.warning(f'[run] Nenhum registro coletado para {data_extracao}')
                    
            
                # Clean data
                if all_data:
                    try:
                        cleaned_data = self.clean_data(all_data)
                        self.logger.info(f"[run] Todos os dados limpos.")
                    except Exception as e:
                        self.logger.error(f"Error cleaning data: {str(e)}")
                        cleaned_data = all_data
                        self.logger.warning("[run] Usando dados originais sem limpeza devido a erro.")
                else:
                    cleaned_data = all_data
                    self.logger.info(f"[run] Nenhum dado para limpeza.")

                # Process based on output type
                if cleaned_data:
                    try:
                        if output_type == "send_dataframe_to_next_step":
                            self.process_and_send_df_to_next_step(cleaned_data)
                            self.logger.info("[run] Dataframe enviado para o próximo step")
                        elif output_type == "upload_to_s3":
                            if bucket_name:
                                self.process_and_upload_to_s3(cleaned_data, bucket_name, prefix)
                    except Exception as e:
                        self.logger.error(f"Error insert S3: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error Inesperado: {str(e)}")


def orchest_handler():
    api_key = os.getenv('x-api-key')
    secret_id = os.getenv('secret_id')
    input_type = orchest.get_step_param('input_type')

    if input_type == "from_step_param":
        # data_extracao = orchest.get_step_param('data_extracao')
        cod_cli_sponte = orchest.get_step_param('cod_cli_sponte')
        is_historical = orchest.get_step_param('is_historical_load')
        sponte_code_list = [cod_cli_sponte]

    elif input_type == "from_incoming_variable":
        # data_extracao = orchest.get_step_param('data_extracao')
        # incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        # is_historical = orchest.get_step_param('is_historical_load')
        # Get data from incoming steps.
        input_data = orchest.get_inputs()
        list_data_extracao = input_data["data"]["date_extract"][endpoint]
        sponte_code_list = input_data["data"]["sponte_code_list"]

    

    handler = SponteAPI(
        logger=logger,
        api_key=api_key,
        secret_id = secret_id
    )
    handler.run(sponte_code_list, list_data_extracao, api_key,secret_id)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)
    api_key = os.getenv('x-api-key')
    secret_id = os.getenv('secret_id')
    # endpoint = 'fatoalunosativos'

    if not api_key:
        raise ValueError(
            "'api_key' must be provided in the configuration.")

    handler = SponteAPI(
        logger=logger,
        api_key=api_key,
        secret_id = secret_id
    )
    handler.run(sponte_code_list, list_data_extracao, api_key,secret_id)

if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()