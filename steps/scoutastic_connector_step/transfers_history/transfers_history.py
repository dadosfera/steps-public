import os
import time
import sys
import json
import logging
from typing import List, Dict, Tuple
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


def get_transfers_page(
    connector: ScoutasticConnector, season: int, page: int, limit: int = 1000
) -> Tuple[List[Dict], bool]:
    """
    Fetches transfer data for a specific season and page.

    Parameters:
        connector (ScoutasticConnector): Connector instance for the API.
        season (int): Season year for the transfer data.
        page_number (int): Page index in the API pagination.
        limit (int): Number of records per page.

    Returns:
        Tuple[List[Dict], bool]: Transfer data and flag indicating the next page.
    """
    endpoint = "players/transfers"
    params = {"season": season, "page": page, "limit": limit}
    try:
        logger.info(f"Fetching transfers - Season: {season}, Page: {page}")

        response = connector.fetch_data(endpoint=endpoint, params=params)
        transfers_data = response.get("docs", [])
        has_next_page = response.get("hasNextPage", False)
        return transfers_data, has_next_page
    except Exception as e:
        logger.error(f"Error fetching page {page} for season {season}: {e}")
        return [], False


def get_incremental_transfers(connector: ScoutasticConnector, season: int) -> List[Dict]:
    """
    Fetches all transfer data for a specific season, handling pagination.

    Parameters:
        connector (ScoutasticConnector): Connector instance for the API.
        season (int): Season year for the transfer data.

    Returns:
        List[Dict]: List of transfer records.
    """
    all_transfers = []
    page = 1

    logger.info(f"Starting transfer extraction for season {season}")

    has_next_page = True

    logger.info(f"Starting transfer extraction for season {season}")
    while True:
        transfers, has_next_page = get_transfers_page(connector, season, page)

        if not transfers:
            logger.info(f"No data found for season {season}, page {page}")
            break

        all_transfers.extend(transfers)
        logger.info(f"Collected {len(transfers)} transfers from page {page}")

        if has_next_page:
            page += 1
            time.sleep(1)
        else:
            logger.info(f"Completed transfer extraction for season {season}")
            break

    logger.info(f"Total transfers collected for season {
                season}: {len(all_transfers)}")
    return all_transfers


def save_to_json_file(transfers_history_data: List[Dict], filename: str):
    """
    Saves transfer data to a JSON file.

    Parameters:
        data (List[Dict]): List of transfer records.
        filename (str): Output JSON file name.

    """
    logger.debug(f"Salvando dados: {transfers_history_data}")
    with open(filename, "w") as f:
        json.dump(transfers_history_data, f)


def orchest_handler():
    """
    Handler function for Orchest Step execution.
    """
    logger.debug("Executing Orchest Handler for Appointments")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    season = int(orchest.get_step_param("season"))

    if not team_identifier or not auth_token or not season:
        raise ValueError(
            "Missing required values: team_identifier, auth_token or season")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    transfers_data = get_incremental_transfers(connector, season)
    save_to_json_file(transfers_data, f"transfers_history_{season}.json")

    logger.info("Appointments data fetched and saved successfully!")


def script_handler():
    """
    Handler function for script execution.
    """
    logger.debug("Executing Script Handler for Appointments")

    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    team_identifier = config["team_identifier"]
    auth_token = config["auth_token"]
    season = int(config.get("season"))

    if not team_identifier or not auth_token or not season:
        raise ValueError(
            "Missing required values: team_identifier, auth_token or season")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    transfers_data = get_incremental_transfers(connector, season)
    save_to_json_file(transfers_data, f"transfers_history_{season}.json")

    logger.info("Transfers History data fetched and saved successfully!")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
