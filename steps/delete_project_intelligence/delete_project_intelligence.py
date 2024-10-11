import json
import logging
import os
import sys
from typing import Tuple, List
import requests

# Configuração de variáveis e logger
ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def delete_project(base_url, project_id, auth_token, auth_username, auth_user_uuid):
    """
    Function to delete a project in the Dadosfera Intelligence by API .

    Parameters:
    base_url (str): Base URL of the API.
    project_id (str): ID of the project to be deleted.
    auth_token (str): User's authentication token.
    auth_username (str): Username associated with the authentication token.
    auth_user_uuid (str): UUID of the authenticated user.

    Returns:
    str: Success or error message based on the request status.
    """

    # Define the full API URL including the project ID
    url = f"{base_url}/async/projects/{project_id}"

    # Define the request headers
    headers = {
        "cookie": f"auth_token={auth_token}; auth_username=\"{auth_username}\"; auth_user_uuid={auth_user_uuid}",
    }

    # Make the DELETE request
    response = requests.delete(url, headers=headers)

    # Check the response status
    if response.status_code == 200:
        return "Project successfully deleted!"
    else:
        return f"Failed to delete the project. Status code: {response.status_code}\nMessage: {response.text}"


def orchest_handler() -> None:
    import orchest
    
    incoming_variable_name = orchest.get_step_param('incoming_variable_name')
    base_url = orchest.get_step_param('base_url')
    auth_token = orchest.get_step_param('auth_token')
    auth_username = orchest.get_step_param('auth_username')
    auth_user_uuid = orchest.get_step_param('auth_user_uuid')

    list_project_id = orchest.get_inputs()[incoming_variable_name]
    
    # Verify if list_project_id is a list of IDs (strings)
    if not isinstance(list_project_id, list) or not all(isinstance(item, str) for item in list_project_id):
        raise ValueError("Erro: 'list_project_id' deve ser uma lista de IDs (números ou strings).")
        
    for project_id in list_project_id:     
        delete_project(base_url = base_url,
                       project_id = project_id,
                       auth_token = auth_token,
                       auth_username = auth_username,
                       auth_user_uuid = auth_user_uuid
                      )
    
    
def script_handler() -> None:
    
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    incoming_variable_name = config['incoming_variable_name']
    base_url = config['base_url']
    auth_token = config['auth_token']
    auth_username = config['auth_username']
    auth_user_uuid = config['auth_user_uuid']
    list_project_id = config['list_project_id']
    
    # Verify if list_project_id is a list of IDs (strings)
    if not isinstance(list_project_id, list) or not all(isinstance(item, str) for item in list_project_id):
        raise ValueError("Erro: 'list_project_id' deve ser uma lista de IDs (números ou strings).")
        
    for project_id in list_project_id:     
        delete_project(base_url = base_url,
                       project_id = project_id,
                       auth_token = auth_token,
                       auth_username = auth_username,
                       auth_user_uuid = auth_user_uuid
                      )
                             

if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Executando como Orchest Step")
        orchest_handler()
    else:
        logger.info("Executando como script")
        script_handler()
