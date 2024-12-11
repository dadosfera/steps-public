import os
import json
import requests
import logging
import orchest

# Configure logger for monitoring and debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Base API URL and authentication token from environment variables
BASE_URL = 'https://api.contact2sale.com/integration'
TOKEN = os.getenv('C2S_PROLAR_TOKEN')


def main():
    """
    Main function to handle the connection to the Contact2Sale API.
    Retrieves the path and parameters from Orchest step parameters,
    constructs the request, and fetches the response.
    """
    # Retrieve API path and query parameters from Orchest's pipeline configuration
    PATH_URL = orchest.get_step_param('c2s_path')
    PARAMS = orchest.get_step_param('params')
    
    # Construct the full URL for the API request
    url = f'{BASE_URL}{PATH_URL}'
    
    # Set up headers for the request, including the Bearer token for authentication
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }

    try:
        # Make the GET request to the API
        logger.debug(f"Making GET request to URL: {url} with parameters: {PARAMS}")
        response = requests.get(url, headers=headers, params=PARAMS)
        
        # Raise an error if the request was unsuccessful
        response.raise_for_status()

        # Log and print the response
        logger.info("Request successful. Response received.")
        logger.debug(f"Response JSON: {response.json()}")
        print(url, PARAMS)
        print(response.json())

    except requests.exceptions.RequestException as e:
        # Log and print errors if the request fails
        logger.error(f"Request failed: {e}")
        raise e

    return response


if __name__ == '__main__':
    main()
