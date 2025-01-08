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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

LAST_UPDATE_PATH = "last_update.json"
PER_PAGE = 50
MAX_REQ_PER_MINUTE = 10


class C2SLead:
    """
    Class to fetch leads from C2S API.

    Attributes:
    - logger: logging.Logger
    - instance_url: str
    - token: str
    """

    def __init__(
        self,
        logger: logging.Logger,
        instance_url: str,
        token: str
    ):
        self.logger = logger
        self.instance_url = instance_url
        self.token = token

    def get_last_update(self):
        """
        Reads the 'last_update' from a JSON file (LAST_UPDATE_PATH).
        Returns None if it doesn't exist or if there's a failure.
        Example: {"last_update": "2024-12-27T10:46:28Z"}
        """
        if not os.path.exists(LAST_UPDATE_PATH):
            self.logger.info(f"[get_last_update] File {
                             LAST_UPDATE_PATH} not found. Returning None.")
            return None

        try:
            with open(LAST_UPDATE_PATH, "r") as f:
                data = json.load(f)
                last_update = data.get("last_update")
                self.logger.info(
                    f"[get_last_update] Loaded last_update {last_update}")
                return last_update
        except Exception as e:
            self.logger.error(f"[get_last_update] Error loading file{
                              LAST_UPDATE_PATH}: {e}")
            return None

    def save_last_update(self, timestamp_str):
        """
        Saves the 'last_update' to a JSON file (LAST_UPDATE_PATH).
        """
        try:
            with open(LAST_UPDATE_PATH, "w") as f:
                json.dump({"last_update": timestamp_str}, f)
            self.logger.info(f"[save_last_update] Saved '{timestamp_str}' to {
                             LAST_UPDATE_PATH} successfully.")
        except Exception as e:
            self.logger.error(f"[save_last_update] Error saving file {
                              LAST_UPDATE_PATH}: {e}")
            raise

    def fetch_data(self, last_update=None):
        """
        Fetches all leads from the C2S API.
        last_update: str - ISO 8601 format (ex.: "2024-12-27T10:46:28Z")
        Returns a list of leads (dicts).
        """
        headers = {
            'Authorization': f'Bearer {self.token}',
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

            if last_update:
                params["updated_gte"] = last_update

            self.logger.info(f"[fetch_data] Requesting page {
                             page}, updated_gte={last_update}")
            try:
                response = requests.get(
                    self.instance_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                leads = data.get("data", [])
                if leads:
                    all_results.extend(leads)
                total = data.get("meta", {}).get("total", 0)

                self.logger.info(f"[fetch_data] Page {page} returned {
                                 len(leads)} leads. Total={total}")

                if (PER_PAGE * page) >= total:
                    self.logger.info(
                        "[fetch_data] Completed fetching all pages.")
                    break

                page += 1
                count += 1

                # api wait 10 req per minute
                if count == MAX_REQ_PER_MINUTE:
                    self.logger.info(
                        "[fetch_data] Rate limit reached: waiting 60 seconds...")
                    time.sleep(60)
                    count = 0

            except requests.exceptions.HTTPError as e:
                self.logger.error(
                    f"[fetch_data] Request failed on page {page}: {e}")
                raise e
            except Exception as e:
                logger.error(
                    f"[fetch_data] Unexpected error on page {page}: {e}")
                raise e

        return all_results

    def find_max_updated_at(self, leads):
        """
        Finds the maximum 'updated_at' timestamp from a list of leads.
        Returns a string in ISO 8601 format (ex.: "2024-12-27T10:46:28Z").
        """
        max_dt = None

        for lead in leads:
            attributes = lead.get("attributes", {})
            lu = attributes.get("updated_at")  # ex.: "2024-12-27T10:46:28Z"
            if lu:
                try:
                    dt = datetime.datetime.fromisoformat(
                        lu.replace("Z", "+00:00"))
                    dt_utc = dt.astimezone(datetime.timezone.utc)
                    if not max_dt or dt > max_dt:
                        max_dt = dt_utc
                except ValueError:
                    # Caso o formato não seja compatível, ignora e segue
                    self.logger.warning(
                        f"[find_max_updated_at] Invalid format:  {lu}")
                    pass

        return max_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if max_dt else None

    def save_to_snowflake(self, snowpark, all_results, table_identifier):
        """
        Receives a list of leads and saves them to Snowflake by Snowpark.
        """
        if not table_identifier:
            self.logger.info(
                "[save_to_snowflake] No table identifier provided. Skipping save operation.")
            return

        try:
            logger.info(
                "[save_to_snowflake] Converting list to Snowpark DataFrame...")
            df_leads = snowpark.createDataFrame(all_results)

            logger.info(f"[save_to_snowflake] Saving DataFrame to table {
                        table_identifier} (append mode)...")
            df_leads.write.mode("append").save_as_table(table_identifier)
            logger.info(f"[save_to_snowflake] DataFrame successfully saved to {
                        table_identifier}.")
        except Exception as e:
            logger.error(
                f"[save_to_snowflake] Error saving data to Snowflake: {e}")
            raise e

    def run(self, snowpark, table_identifier=None):
        """
        Main method to orchestrate the process.
        """

        try:
            last_update = self.get_last_update()
            if last_update:
                self.logger.info(
                    f"[run] Incremental load from updated_at={last_update}")
            else:
                self.logger.info("[run] Full load - No 'last_update' found.")

            leads = self.fetch_data(last_update)
            logger.info(f"[main] Total leads fetched: {len(leads)}")

            if leads:
                new_last_update = self.find_max_updated_at(leads)
                if new_last_update:
                    self.save_last_update(new_last_update)
                else:
                    self.logger.info(
                        "[run] No valid 'updated_at' found to save.")

                self.save_to_snowflake(snowpark, leads, table_identifier)

        except Exception as e:
            self.logger.error(f"Error occured: {e}")
            raise


def orchest_handler():
    base_url = orchest.get_step_param('url')
    token = os.getenv("C2S_AUTHENTICATOR_TOKEN")
    table_identifier = orchest.get_step_param('table_identifier')

    if not token:
        raise Exception("C2S_AUTHENTICATOR_TOKEN is required")

    handler = C2SLead(
        logger=logger,
        instance_url=base_url,
        token=token
    )
    snowpark = get_snowpark_session(os.getenv("SECRET_ID"))
    handler.run(snowpark, table_identifier)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception(
            "Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    base_url = config.get("url")
    token = config.get("token")
    table_identifier = config.get("table_identifier")

    if not base_url or not token:
        raise ValueError(
            "Both 'url' and 'token' must be provided in the configuration.")

    handler = C2SLead(
        logger=logger,
        instance_url=base_url,
        token=token
    )
    snowpark = get_snowpark_session(os.getenv("SECRET_ID"))
    handler.run(snowpark, table_identifier)


if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
