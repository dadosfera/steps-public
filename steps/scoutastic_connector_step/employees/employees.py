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


def get_employees_page(connector: ScoutasticConnector, page_number: int) -> List[Dict]:
    """
    Fetches a single page of employees data.

    Parameters:
        connector (ScoutasticConnector): API connector instance.
        page_number (int): Page number for pagination.

    Returns:
        List[Dict]: List of employees on the current page.
    """
    endpoint = "employees"
    params = {"deleted": "false", "page": page_number}
    try:
        logger.info(f"Fetching employees - Page: {page_number}")
        response = connector.fetch_data(endpoint=endpoint, params=params)
        data = response.get("docs", [])
        return data
    except Exception as e:
        logger.error(f"Error fetching employees on page {page_number}: {e}")
        return []


def get_all_employees(connector: ScoutasticConnector) -> List[Dict]:
    """
    Fetches all employees data, handling pagination.

    Parameters:
        connector (ScoutasticConnector): API connector instance.

    Returns:
        List[Dict]: List of all employees.
    """

    all_employees = []
    page_number = 1
    max_retries = 5
    retry_count = 0

    while True:
        try:
            employees = get_employees_page(connector, page_number)
            if employees:
                all_employees.extend(employees)
                page_number += 1
            else:
                logger.info(
                    f"No employees found in page {
                        page_number}. Exiting the loop..."
                )
                break
        except (HTTPError, ChunkedEncodingError) as e:
            logger.info(
                f"Erro in getting data for page {
                    page_number}. Retrying ({retry_count+1}/{max_retries})..."
            )
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Max attempts exceeded. Exiting the loop...")
                break

            time.sleep(5)

    logger.info("Total employees found:", len(all_employees))
    return all_employees


def save_to_json_file(employee_data: List[Dict], filename: str):
    """
    Saves employee data to a JSON file.

    Parameters:
        data (List[Dict]): List of employee records.
        filename (str): Output JSON file name.

    """
    logger.debug(f"Salvando dados: {employee_data}")
    with open(filename, "w") as f:
        json.dump(managers_data, f)


def orchest_handler():
    """
    Orchest step handler for extracting employee data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")

    if not auth_token or not team_identifier:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN or team_identifier")

    logger.info(f"Parameters received - team_identifier: {team_identifier}")

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    # Fetch and save employees
    employees_data = get_all_employees(connector)
    save_to_json_file(employees_data, "employees_data.json")


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

    if not auth_token or not team_identifier:
        raise ValueError(
            "Missing required parameters: auth_token or team_identifier")

    logger.info(f"Parameters received - team_identifier: {team_identifier}")

    connector = ScoutasticConnector(
        auth_token=auth_token, team_identifier=team_identifier)

    # Fetch and save employees
    employees_data = get_all_employees(connector)
    save_to_json_file(employees_data, "employees_data.json")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
