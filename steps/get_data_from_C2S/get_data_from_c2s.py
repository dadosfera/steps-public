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
    
    all_results = []

    # Check if the path is for 'leads' and if 'page' is a list
    if 'leads' in PATH_URL and isinstance(PARAMS.get('page'), list) and PARAMS['page']:
        # Iterate through the list of pages and collect data
        for page in PARAMS['page']:
            # Update the page parameter for the current page in the iteration
            PARAMS['page'] = page
            
            try:
                # Make the GET request to the API
                logger.debug(f"Making GET request to URL: {url} with parameters: {PARAMS}")
                response = requests.get(url, headers=headers, params=PARAMS)

                # Log and accumulate the results
                logger.info(f"Request successful for page {page}.")
                data = response.json()
                # logger.debug(f"Response JSON: {data}")

                if data.get('data'):
                    all_results.extend(data['data'])


            except requests.exceptions.RequestException as e:
                # Log and print errors if the request fails
                logger.error(f"Request failed for page {page}: {e}")
                raise e

        # Return the accumulated results after processing all pages
        logger.debug(f"Response JSON: {all_results}")

        # Save the result as an output for the next pipeline step
        orchest.output(all_results, name="response")

    else:
        try:
            # Make the GET request to the API
            logger.debug(f"Making GET request to URL: {url} with parameters: {PARAMS}")
            response = requests.get(url, headers=headers, params=PARAMS)
            
            # Raise an error if the request was unsuccessful
            response.raise_for_status()

            # Log the response
            logger.info("Request successful. Response received.")
            logger.debug(f"Response JSON: {response.json()}")

        except requests.exceptions.RequestException as e:
            # Log errors if the request fails
            logger.error(f"Request failed: {e}")
            raise e

        # Save the result as an output for the next pipeline step
        orchest.output(response.json(), name="response")


if __name__ == '__main__':
    main()
