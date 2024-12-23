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


def get_players_data(connector: ScoutasticConnector, team_ids: List[str]) -> List[Dict]:
    """
    Fetches player data for all specified team IDs from the Scoutastic API.

    Parameters:
        connector (ScoutasticConnector): API connector instance.
        team_ids (List[str]): List of team IDs.

    Returns:
        List[Dict]: Players data.
    """
    output_players = []

    for team_id in team_ids:
        page = 1
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            params = {
                "teamId": team_id,
                "marketValues": "true",
                "performanceData": "true",
                "debuts": "true",
                "injuryData": "true",
                "gender": "male",
                "limit": 100,
                "fastMode": "false",
                "page": page,
            }

            try:
                logger.info(f"Fetching players for team {
                            team_id}, page {page}")
                response = connector.fetch_data(
                    endpoint="players", params=params)

                if response:
                    players = response.get("docs", [])

                output_players.extend(players)
                logger.info(f"Collected {len(players)} players from page {
                            page} for team {team_id}.")

                # Verifica se há mais páginas
                if not response.get("hasNextPage", False):
                    logger.info(f"All players processed for team {team_id}.")
                    break

                page += 1
                time.sleep(1)  # Evita exceder a taxa de requisições
            except Exception as e:
                logger.warning(
                    f"Error fetching players for team {team_id}, page {page}: {
                        e}. Retrying ({retry_count+1}/{max_retries})..."
                )
                retry_count += 1
                time.sleep(5)
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for team {
                                 team_id}, page {page}. Skipping...")
                    break

    logger.info(f"Total players collected: {len(output_players)}")
    return output_players


def save_to_json_file(data: List[Dict]):
    """
    Saves player data to a JSON file.

    Parameters:
        data (List[Dict]): List of player records.
    """
    logger.info("Saving data to players_data.json")

    if not data:
        logger.warning("No data to save. File will not be created.")
        return

    try:
        with open("players_data.json", "w") as f:
            json.dump(data, f)
        logger.info("Data successfully saved to players_data.json")
    except Exception as e:
        logger.error(f"Error saving data to players_data.json: {e}")


def orchest_handler():
    """
    Orchest step handler for extracting player data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    team_ids = orchest.get_step_param("team_id")

    team_id_list = [id.strip().upper()
                    for id in team_ids.split(",") if id.strip()]

    if not auth_token or not team_identifier or not team_ids:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN, team_identifier and team_ids")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    players_data = get_players_data(connector, team_id_list)
    save_to_json_file(players_data)


def script_handler():
    """
    Script handler for standalone execution.
    """
    logger.info("Running as standalone script")

    if len(sys.argv) != 2:
        raise ValueError("Please provide configuration JSON as an argument")

    config = json.loads(sys.argv[1])

    auth_token = config.get("auth_token")
    team_identifier = config.get("team_identifier")
    team_ids = config.get("team_ids")

    team_id_list = [id.strip().upper()
                    for id in team_ids.split(",") if id.strip()]

    if not auth_token or not team_identifier or not team_ids:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN, team_identifier and team_ids")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    players_data = get_players_data(connector, team_id_list)
    save_to_json_file(players_data)


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
