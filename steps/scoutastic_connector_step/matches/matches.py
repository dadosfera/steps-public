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


def get_matches_by_competition(connector: ScoutasticConnector, competition_id: str) -> List[Dict]:
    """
    Fetches all matches for a specific competition, handling pagination.

    Parameters:
        connector (ScoutasticConnector): API connector instance.
        competition_id (str): ID of the competition.

    Returns:
        List[Dict]: List of match records for the competition.
    """
    all_matches = []
    page = 1

    while True:
        endpoint = "matches"
        params = {
            "competitionId": competition_id,
            "fastMode": "false",
            "gender": "male",
            "page": page,
        }
        try:
            logger.info(f"Fetching matches for competition {
                        competition_id}, page {page}")
            response = connector.fetch_data(endpoint=endpoint, params=params)
            matches = response.get("docs", [])

            if not matches:
                logger.info(f"No more matches found for competition {
                            competition_id} on page {page}.")
                break

            all_matches.extend(matches)
            logger.info(f"Collected {len(matches)} matches from page {page}")
            page += 1
            time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.error(f"Error fetching matches for competition {
                         competition_id} on page {page}: {e}")
            break

    logger.info(f"Total matches collected for competition {
                competition_id}: {len(all_matches)}")
    return all_matches


def get_all_matches(connector: ScoutasticConnector, competitions: List[str]) -> List[Dict]:
    """
    Fetches matches for all competitions.

    Parameters:
        connector (ScoutasticConnector): API connector instance.
        competitions (List[str]): List of competition IDs.

    Returns:
        List[Dict]: List of all match records.
    """
    all_matches = []
    for competition_id in competitions:
        logger.info(f"Processing competition {competition_id}")
        matches = get_matches_by_competition(connector, competition_id)
        all_matches.extend(matches)
    logger.info(f"Total matches collected for all competitions: {
                len(all_matches)}")
    return all_matches


def save_to_json_file(data: List[Dict], filename: str):
    """
    Saves match data to a JSON file.

    Parameters:
        data (List[Dict]): List of match records.
        filename (str): Output JSON file name.
    """
    try:
        with open(filename, "w") as f:
            json.dump(data, f)
        logger.info(f"Match data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save match data to {filename}: {e}")


def orchest_handler():
    """
    Orchest step handler for extracting match data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    competitions = orchest.get_step_param("competitions")

    competitions = [id.strip().upper()
                    for id in competitions.split(",") if id.strip()]

    if not auth_token or not team_identifier or not competitions:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN, team_identifier, or competitions")

    logger.info(
        f"Parameters received - team_identifier: {team_identifier}, competitions: {competitions}")

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    # Fetch and save matches
    matches_data = get_all_matches(connector, competitions)
    save_to_json_file(matches_data, "matches_data.json")


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
    competitions = config.get("competitions", [])

    if not auth_token or not team_identifier or not competitions:
        raise ValueError(
            "Missing required parameters: auth_token, team_identifier, or competitions")

    logger.info(
        f"Parameters received - team_identifier: {team_identifier}, competitions: {competitions}")

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    # Fetch and save matches
    matches_data = get_all_matches(connector, competitions)
    save_to_json_file(matches_data, "matches_data.json")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
