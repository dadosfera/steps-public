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
logger.setLevel(logging.DEBUG)


logger.debug("Starting Scoutastic Connector Step")

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

logger.debug("Importing appointments module")


def get_appointments_data(connector: ScoutasticConnector) -> List[Dict]:
    """
    Fetches all appointments data from the Scoutastic API.

    Parameters
    ----------
    connector : ScoutasticConnector
        Instance of the connector for the Scoutastic API.

    Returns
    -------
    List[Dict]
        List of all fetched appointments as dictionaries.
    """
    appointments = []
    max_retries = 5
    page = 1

    logger.info("Starting to fetch all appointments data.")

    while True:
        api_link = f"{connector.base_url}/appointments?page={page}"
        logger.info(f"Fetching appointments from page {page}: {api_link}")

        retry_count = 0
        passed = False

        while not passed and retry_count < max_retries:
            try:
                response = connector.session.get(api_link)
                response.raise_for_status()  # Raise HTTPError for bad responses
                logger.info(
                    f"Successfully fetched appointments from page {page}")
                passed = True
            except (HTTPError, ChunkedEncodingError) as e:
                logger.warning(f"Request error: {e}. Retrying in 5 seconds... ({
                               retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(5)

        if not passed:
            logger.error(f"Failed to fetch appointments data after {
                         max_retries} retries.")
            break

        try:
            apps = response.json()
            logger.debug(f"Response data: {apps}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            break

        fetched_apps = apps.get('docs', [])
        appointments.extend(fetched_apps)
        logger.debug(f"Total appointments fetched so far: {len(appointments)}")

        if apps.get('hasNextPage'):
            page += 1
            logger.info(f"Proceeding to the next page: {page}")
        else:
            logger.info("No more pages to fetch for appointments.")
            break

    return appointments


def save_appointments_to_json(appointments: List[Dict]):
    """
    Saves match and player appointments to separate JSON files.
    """
    logger.debug(f"Salvando dados: {appointments}")
    with open("appointments_data.json", "w") as f:
        json.dump(appointments, f)


def orchest_handler():
    """
    Handler function for Orchest Step execution.
    """
    logger.debug("Executing Orchest Handler for Appointments")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")

    if not team_identifier or not auth_token:
        raise ValueError(
            "Missing required values: team_identifier or auth_token")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    appointments = get_appointments_data(connector)
    save_appointments_to_json(appointments)

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

    if not team_identifier or not auth_token:
        raise ValueError(
            "Missing required values: team_identifier or auth_token")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    appointments = get_appointments_data(connector)
    save_appointments_to_json(appointments)

    logger.info("Appointments data fetched and saved successfully!")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
