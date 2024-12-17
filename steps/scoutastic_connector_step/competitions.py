import os
import time
import sys
import logging
import json
from typing import List, Dict
from requests.exceptions import HTTPError, ChunkedEncodingError
from connector import ScoutasticConnector
import orchest

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


def get_competitions_data(connector: ScoutasticConnector, competitions: List[str]) -> List[Dict]:
    """
    Obtém dados de competições usando o conector genérico.
    
    Parameters
    ----------
    connector : ScoutasticConnector
        Instância do conector para a Scoutastic API.
    competitions : List[str]
        Lista de IDs de competições a serem consultadas.
    
    Returns
    -------
    output_competitions : List[Dict]
        Dados das competições.
    """

    output_competitions = []
    max_retries = 5
    
    logger.info(f"Lista de competições a serem processadas: {competitions}")

    for competition in competitions:
        logger.info(f"Coletando dados para competition_id: {competition}")

        retry_count = 0
        while retry_count < max_retries:
            try:
                # Faz a requisição usando o conector Scoutastic
                data = connector.fetch_data(endpoint=f"competitions/{competition}", params={"teamIds": "false"})
                if data:
                    output_competitions.append(data)
                    logger.info(f"Dados obtidos para {competition}: {data}")
                else:
                    logger.warning(f"Sem dados retornados para {competition}.")
                break                    
            except (HTTPError, ChunkedEncodingError) as e:
                logger.warning(f"Error ao buscar dados para {competition}: {e}. Tentando novamente ({retry_count+1}/{max_retries})...")
                retry_count += 1
                time.sleep(5)

    logger.info("Dados extraídos!")
    return output_competitions


def save_to_json_file(output_competitions):
    """
    Salva em um arquivo JSON com indentação para melhor legibilidade
    """
    logger.debug(f"Salvando dados: {output_competitions}")  
    with open("competitions_data.json", "w") as f:
        json.dump(output_competitions, f)


def orchest_handler():
    
    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    competitions_ids = orchest.get_step_param("competitions_ids")
    
    competitions_list = [id.strip().upper() for id in competitions_ids.split(",") if id.strip()]
    print(competitions_list)
    
    if not team_identifier or not competitions_ids or not auth_token:
        raise ValueError("Valores requeridos faltantes: team_identifier, competitions_ids, or auth_token")
    
    connector = ScoutasticConnector(
        auth_token=auth_token, 
        team_identifier=team_identifier
    )

    data = get_competitions_data(connector, competitions_list)
    logger.info(f"Dados coletados: {data}")
    save_to_json_file(data)
    logger.info("Dados das competições salvas com sucesso!")


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)
    
    team_identifier = config["team_identifier"] 
    competitions_ids = config["competitions_ids"]   
    auth_token = config["auth_token"]

    if not team_identifier or not competitions_ids or not auth_token:
        raise ValueError("Valores requeridos faltantes: team_identifier, competitions_ids, or auth_token")

    competitions_list = [id.strip().upper() for id in competitions_ids.split(",") if id.strip()]  # Definindo competitions_list
        
    connector = ScoutasticConnector(
        auth_token=auth_token, 
        team_identifier=team_identifier
    )

    data = get_competitions_data(connector, competitions_list)
    logger.info(f"Dados coletados: {data}")
    save_to_json_file(data)
    logger.info("Dados das competições salvas com sucesso!")
    
    
if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()