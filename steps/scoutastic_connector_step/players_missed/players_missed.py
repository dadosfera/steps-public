import os
import time
import sys
import json
import logging
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


def get_players_missed_data(connector: ScoutasticConnector, player_ids: List[str]) -> List[Dict]:
    """
    Fetches missed player data for the specified player IDs from the Scoutastic API.

    Parameters:
        connector (ScoutasticConnector): API connector instance.
        player_ids (List[str]): List of player IDs.

    Returns:
        List[Dict]: Player data for the missed players.
    """
    output_players_missed = []

    for player_id in player_ids:
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            params = {
                "debuts": "true",
                "marketValues": "true",
                "performanceData": "true",
                "injuryData": "true",
                "fastMode": "false",
            }

            try:
                logger.info(f"Fetching data for missed player ID: {player_id}")
                response = connector.fetch_data(
                    endpoint=f"players/{player_id}", params=params)

                if not response:
                    logger.warning(f"No data found for player ID: {
                                   player_id}. Retrying...")
                    retry_count += 1
                    time.sleep(5)
                    continue

                output_players_missed.append(response)
                logger.info(f"Collected data for player ID: {player_id}")
                break
            except Exception as e:
                logger.warning(
                    f"Error fetching data for player ID: {player_id}: {
                        e}. Retrying ({retry_count+1}/{max_retries})..."
                )
                retry_count += 1
                time.sleep(5)

            if retry_count >= max_retries:
                logger.error(f"Max retries reached for player ID: {
                             player_id}. Skipping...")

    logger.info(f"Total missed players collected: {
                len(output_players_missed)}")
    return output_players_missed


def save_to_json_file(data: List[Dict]):
    """
    Salva os dados coletados em um arquivo JSON.
    """
    with open("players_missed_data.json", "w") as f:
        json.dump(data, f)


def orchest_handler():
    """
    Orchest step handler para coleta de jogadores ausentes.
    """

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    player_ids = orchest.get_step_param("player_ids")

    player_ids_list = [id.strip().upper()
                       for id in player_ids.split(",") if id.strip()]

    if not auth_token or not team_identifier or not player_ids:
        raise ValueError(
            "Parâmetros obrigatórios ausentes: SCOUTASTIC_TOKEN, team_identifier ou player_ids")

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    players_missed = get_players_missed_data(connector, player_ids_list)

    # Salvar dados
    save_to_json_file(players_missed)


def script_handler():
    """
    Script handler para execução standalone.
    """
    logger.info("Executando como script standalone")

    if len(sys.argv) != 2:
        raise ValueError("Passe a configuração JSON como argumento")

    config = json.loads(sys.argv[1])

    auth_token = config.get("auth_token")
    team_identifier = config.get("team_identifier")
    player_ids = config.get("player_ids", "").split(",")

    if not auth_token or not team_identifier or not player_ids:
        raise ValueError(
            "Parâmetros obrigatórios ausentes: auth_token, team_identifier ou player_ids")

    player_ids_list = [id.strip().upper()
                       for id in player_ids.split(",") if id.strip()]

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    # Buscar dados dos jogadores ausentes
    players_missed = get_players_missed_data(connector, player_ids_list)

    # Salvar dados
    save_to_json_file(players_missed)


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
