import os
import requests
from requests.exceptions import HTTPError
import logging
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlencode


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScoutasticConnector:
    """
    Connector for the Scoutastic API, responsible for:
    - Authentication
    - Building URLs for different endpoints
    - Fetching data from the API
    """

    def __init__(self, auth_token: str, team_identifier: str):
        """
        Initializes the connector for the Scoutastic API.
        Parameters:
            team_identifier: Team identifier (e.g., "galo")
            auth_token: Authentication token in the format "Bearer <token>"
        """
        self.team_identifier = team_identifier
        self.base_url = f"https://{self.team_identifier}.scoutastic.com/api/v1"
        self.auth_token = auth_token

        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.auth_token})


    def build_url(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Constructs a URL for a specific endpoint with optional parameters.
        Parameters:
            endpoint: API endpoint.
            params: Request parameters.
        Returns:
            Complete URL for the request.
        """
        url = f"{self.base_url}/{endpoint}"
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        logger.debug(f"Built URL: {url}")
            
        return url


    def fetch_data(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Makes a GET request to the specified endpoint with optional parameters.
        Parameters:
            endpoint: API endpoint.
            params: Request parameters.
        Returns:
            Dictionary containing the response data.
        """
        try:
            url = self.build_url(endpoint, params)
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url)
            logger.debug(f"Response status code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Response data: {data}")
                return data
            else:
                logger.error(f"Failed to fetch data from {url}. Status: {response.status_code}")
                response.raise_for_status()
        except HTTPError as e:
            logger.error(f"HTTP error occurred while fetching data from {url}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error occurred while accessing {url}: {e}")
            raise e





