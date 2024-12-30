import os
import sys
import json
import time
import datetime
import requests
from typing import List, Dict
import logging
import orchest
from dadosfera.services.snowflake import get_snowpark_session


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


BASE_URL = orchest.get_step_param('url')
TOKEN = os.getenv('C2S_AUTHENTICATOR_TOKEN')


LAST_UPDATE_PATH = "last_update.json"
PER_PAGE = 50
MAX_REQ_PER_MINUTE = 10


def get_last_update():
    """
    Lê o 'last_update' de um arquivo JSON (LAST_UPDATE_PATH).
    Retorna None se não existir ou se houver falha.
    Exemplo: {"last_update": "2024-12-27T10:46:28Z"}
    """
    if not os.path.exists(LAST_UPDATE_PATH):
        logger.info(f"[get_last_update] Arquivo {
                    LAST_UPDATE_PATH} não encontrado. Retornando None.")
        return None

    try:
        with open(LAST_UPDATE_PATH, "r") as f:
            data = json.load(f)
            last_update = data.get("last_update")
            logger.info(
                f"[get_last_update] last_update carregado: {last_update}")
            return last_update
    except Exception as e:
        logger.error(f"[get_last_update] Erro ao carregar o arquivo {
                     LAST_UPDATE_PATH}: {e}")
        return None


def save_last_update(timestamp_str):
    """
    Salva o timestamp (ex.: '2024-01-01T00:00:00Z') em arquivo JSON.
    """
    try:
        with open(LAST_UPDATE_PATH, "w") as f:
            json.dump({"last_update": timestamp_str}, f)
        logger.info(f"[save_last_update] Valor '{
                    timestamp_str}' salvo com sucesso em {LAST_UPDATE_PATH}.")
    except Exception as e:
        logger.error(f"[save_last_update] Erro ao salvar no arquivo {
                     LAST_UPDATE_PATH}: {e}")
        raise


def fetch_data(last_update=None):
    """
    Faz a chamada à API, usando 'updated_gte' como filtro se existir.
    Retorna a lista de leads.
    Respeita a limitação de 10 requisições por minuto.
    """
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'

    }
    all_results = []
    page = 1
    count = 0

    while True:
        params = {
            "page": page,
            "perpage": PER_PAGE
        }
        # Só adiciona last_update se existir (ou seja, se não for a primeira execução).
        if last_update:
            params["updated_gte"] = last_update

        logger.info(f"[fetch_data] Requisição página {
                    page}, updated_gte={last_update}")
        try:
            response = requests.get(BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            leads = data.get("data", [])
            if leads:
                all_results.extend(leads)
            total = data.get("meta", {}).get("total", 0)

            logger.info(f"[fetch_data] Página {page} retornou {
                        len(leads)} leads. total={total}")

            # Se a paginação estiver concluída, saímos do loop
            if (PER_PAGE * page) >= total:
                logger.info(
                    "[fetch_data] Finalizando a coleta (todas as páginas)...")
                break

            page += 1
            count += 1

            # api wait 10 req per minute
            if count == MAX_REQ_PER_MINUTE:
                logger.info(
                    "[fetch_data] Limite de 10 req/min atingido: aguardando 60 segundos...")
                time.sleep(60)
                count = 0

        except requests.exceptions.HTTPError as e:
            logger.error(f"[fetch_data] Request falhou na página {page}: {e}")
            raise e
        except Exception as e:
            logger.error(f"[fetch_data] Erro inesperado na página {page}: {e}")
            raise e

    return all_results


def find_max_updated_at(leads):
    """
    Percorre a lista de leads e identifica o maior valor de 'updated_at'.
    Retorna o timestamp no formato 'YYYY-MM-DDTHH:MM:SSZ'.
    """
    max_dt = None

    for lead in leads:
        attributes = lead.get("attributes", {})
        lu = attributes.get("updated_at")  # ex.: "2024-12-27T10:46:28Z"
        if lu:
            try:
                dt = datetime.datetime.fromisoformat(lu.replace("Z", "+00:00"))
                dt_utc = dt.astimezone(datetime.timezone.utc)
                if not max_dt or dt > max_dt:
                    max_dt = dt_utc
            except ValueError:
                # Caso o formato não seja compatível, ignora e segue
                logger.warning(f"[find_max_updated_at] Formato inválido: {lu}")
                pass

    if max_dt:
        formatted = max_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return formatted
    return None


def save_to_snowflake(snowpark, all_results):
    """
    Recebe a lista de leads (all_results) e salva no Snowflake via Snowpark.
    """
    try:
        logger.info(
            "[save_to_snowflake] Convertendo lista em DataFrame Snowpark...")
        df_leads = snowpark.createDataFrame(all_results)

        table_identifier = "DADOSFERA_PRD_IBRAM.PROLAR.TB_RAW_LEADS"
        logger.info(f"[save_to_snowflake] Salvando DataFrame na tabela {
                    table_identifier} (modo append)...")
        df_leads.write.mode("append").save_as_table(table_identifier)
        logger.info(f"[save_to_snowflake] DataFrame salvo com sucesso em {
                    table_identifier}.")
    except Exception as e:
        logger.error(
            f"[save_to_snowflake] Erro ao salvar dados no Snowflake: {e}")
        raise e


def main():
    """
    Fluxo principal
    """
    secret_id = os.getenv("SECRET_ID")
    snowpark = get_snowpark_session(secret_id)
    snowpark.use_warehouse('COMPUTE_WH')
    snowpark.use_schema('PROLAR')

    try:
        last_update = get_last_update()
        if last_update:
            logger.info(
                f"[main] INCREMENTAL a partir de updated_at={last_update}")
        else:
            logger.info("[main] FULL LOAD - Nenhum 'last_update' encontrado")

        leads = fetch_data(last_update)
        logger.info(f"[main] Total de registros obtidos: {len(leads)}")

        if leads:
            save_to_snowflake(snowpark, leads)
            logger.info("[main] Salvando leads no Snowflake...")

            new_last_update = find_max_updated_at(leads)
            logger.info(f"[main] Valor encontrado: {new_last_update}")

            if new_last_update:
                save_last_update(new_last_update)
                logger.info(f"[main] Arquivo '{LAST_UPDATE_PATH}' atualizado.")
            else:
                logger.info(
                    "[main] Nenhum 'updated_at' válido encontrado; nada a salvar.")

        else:
            logger.info("[main] Nenhum lead retornado.")

    except Exception as e:
        logger.info(f"Ocorreu um erro: {e}")
        raise
    finally:
        snowpark.close()


if __name__ == "__main__":

    main()
