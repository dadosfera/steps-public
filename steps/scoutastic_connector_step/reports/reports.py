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


def get_all_reports(connector: ScoutasticConnector) -> List[Dict]:
    """
    Fetches all reports from the Scoutastic API.

    Parameters:
        connector (ScoutasticConnector): API connector instance.

    Returns:
        List[Dict]: List of all reports.
    """
    all_reports = []
    page_number = 1
    max_retries = 5

    while True:
        retry_count = 0

        while retry_count < max_retries:
            params = {"page": page_number}
            try:
                logger.info(f"Fetching reports, page {page_number}")
                response = connector.fetch_data(
                    endpoint="reports", params=params)

                if not response or "docs" not in response:
                    logger.warning(f"No data on page {
                                   page_number}. Exiting loop.")
                    return all_reports

                reports = response.get("docs", [])
                if not reports:
                    logger.info(f"No more reports on page {page_number}.")
                    return all_reports

                all_reports.extend(reports)
                logger.info(f"Collected {len(reports)
                                         } reports from page {page_number}.")

                # Verifica se há próxima página
                if not response.get("hasNextPage", False):
                    logger.info(
                        "Todas as páginas processadas. Encerrando coleta.")
                    return all_reports

                page_number += 1
                break
            except (HTTPError, ChunkedEncodingError) as e:
                logger.warning(
                    f"Error fetching reports on page {page_number}: {
                        e}. Retry ({retry_count+1}/{max_retries})..."
                )
                retry_count += 1
                time.sleep(5)

    logger.info("Coleta de relatórios finalizada!")
    return all_reports


def save_to_json_file(all_reports):
    """
    Saves report data to a JSON file.
    """
    logger.debug(f"Tentando salvar os dados no arquivo {all_reports}")
    with open("reports_data.json", "w") as f:
        json.dump(all_reports, f)


def orchest_handler():
    """
    Orchest step handler for extracting report data.
    """
    logger.info("Running as Orchest Step")

    auth_token = os.getenv("SCOUTASTIC_TOKEN")
    team_identifier = orchest.get_step_param("team_identifier")

    if not auth_token or not team_identifier:
        raise ValueError(
            "Missing required parameters: SCOUTASTIC_TOKEN or team_identifier")

    logger.info(f"Parameters received - team_identifier: {team_identifier}")

    connector = ScoutasticConnector(
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    # Fetch reports
    reports = get_all_reports(connector)
    if not reports:
        logger.warning("No reports found. Nothing to save.")
        return

    # Save reports to JSON
    save_to_json_file(reports)


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
        auth_token=auth_token,
        team_identifier=team_identifier
    )

    reports = get_all_reports(connector)
    if not reports:
        logger.warning("No reports found. Nothing to save.")
        return

    save_to_json_file(reports)


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
