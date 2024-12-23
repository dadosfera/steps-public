import os
import json
import time
import logging
from typing import List, Dict
from connector import ScoutasticConnector
import orchest
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


def get_teams_data(connector: ScoutasticConnector, competitions: List[str]) -> List[Dict]:
    """
    Fetches teams data for all specified competitions from the Scoutastic API.
    """
    output_teams = []

    for competition_id in competitions:
        page = 1
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            params = {"competitionId": competition_id,
                      "gender": "male", "page": page}
            try:
                logger.info(f"Fetching teams for competition {
                            competition_id}, page {page}")
                response = connector.fetch_data(
                    endpoint="teams", params=params)

                if response:
                    teams_data = response.get("docs", [])
                    if teams_data:
                        for team in teams_data:
                            team["mainCompetitionExternalId"] = competition_id
                        output_teams.extend(teams_data)
                        logger.info(f"Collected {len(teams_data)} teams for competition {
                                    competition_id}")
                    else:
                        logger.info(f"No teams found for competition {
                                    competition_id}.")
                    break
                else:
                    logger.warning(f"No response for competition {
                                   competition_id}. Retrying...")
                    retry_count += 1
                    time.sleep(5)
            except (HTTPError, ChunkedEncodingError) as e:
                logger.warning(f"Error in getting data for competition {competition_id}: {
                               e}. Retrying ({retry_count+1}/{max_retries})...")
                retry_count += 1
                time.sleep(5)

            if retry_count >= max_retries:
                logger.error(f"Max retries reached for competition {
                             competition_id}. Skipping...")
                break

    logger.info(f"Total teams collected: {len(output_teams)}")
    return output_teams


def save_to_json_file(output_teams):
    """
    Saves team data to a JSON file.
    """
    try:
        with open("teams_data.json", "w") as f:
            json.dump(output_teams, f)
        logger.info("File saved successfully: teams_data.json")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")


def orchest_handler():
    """
    Orchest step handler for extracting team data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")
    competitions_ids = orchest.get_step_param("competitions_ids")

    competitions = [id.strip().upper()
                    for id in competitions_ids.split(",") if id.strip()]

    if not auth_token or not team_identifier or not competitions_ids:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN, team_identifier, or competitions")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    teams = get_teams_data(connector, competitions)
    if not teams:
        logger.warning("No team data found. Nothing to save.")
        return

    save_to_json_file(teams)


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
    competitions_ids = config.get("competitions")

    competitions = [id.strip().upper()
                    for id in competitions_ids.split(",") if id.strip()]

    if not auth_token or not team_identifier or not competitions:
        raise ValueError(
            "Missing required parameters: auth_token, team_identifier, or competitions")

    logger.info(
        f"Parameters received - team_identifier: {team_identifier}, competitions: {competitions}")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    teams = get_teams_data(connector, competitions)
    if not teams:
        logger.warning("No team data found. Nothing to save.")
        return

    save_to_json_file(teams)


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
