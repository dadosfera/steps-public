import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build


ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")
SCOPES = ["https://www.googleapis.com/auth/drive"]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def authenticate_google_drive(service_account_file: Path) -> Resource:
    """
    Gets authenticated Google Drive service account.

    Parameters
    ----------
    service_account_file: Path
        Json credentials service account path.

    Returns
    -------
    service: Resource
        Google Drive service account.
    """

    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )

    service = build("drive", "v3", credentials=credentials)
    return service


def list_files_in_folder(service: Resource, selected_folder_id: str) -> List[Dict]:
    """
    Gets all files in selected Google Drive folder.

    Parameters
    ----------
    service: Resource
        Google Drive service account.
    selected_folder_id: str
        Selected Google Drive folder ID.

    Returns
    -------
    outputs: List[Dict]
        List with all files from Google Drive folder.
    """

    results = (
        service.files()
        .list(
            q=f"'{selected_folder_id}' in parents and trashed=false",
            pageSize=10,
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )

    logger.info(f"Selected folder id {selected_folder_id}")
    files = results.get("files", [])

    outputs = []
    for file in files:
        file_name = file["name"]
        file_id = file["id"]

        request = service.files().get_media(fileId=file_id)
        content = request.execute()

        outputs.append({"file_name": file_name, "file_content": content})

    return outputs


def orchest_handler():
    import orchest

    service_account_file = orchest.get_step_param("service_account_file")
    selected_folder_id = orchest.get_step_param("selected_folder_id")
    outgoing_variable_name = orchest.get_step_param("outgoing_variable_name")

    service = authenticate_google_drive(service_account_file)
    outputs = list_files_in_folder(service, selected_folder_id)

    orchest.output(data=outputs, name=outgoing_variable_name)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")

    config_json = sys.argv[1]
    config = json.loads(config_json)

    service_account_file = config["service_account_file"]
    selected_folder_id = config["selected_folder_id"]
    output_file_location = config["output_file_location"]

    service = authenticate_google_drive(service_account_file)
    outputs = list_files_in_folder(service, selected_folder_id)

    failed_saves = []

    for object_ in outputs:
        file_name = object_["file_name"]
        file_content = object_["file_content"]

        file_path = os.path.join(output_file_location, file_name)

        try:
            if isinstance(file_content, bytes):
                with open(file_path, "wb") as f:
                    f.write(file_content)

            elif isinstance(file_content, str):
                with open(file_path, "w") as f:
                    f.write(file_content)
            else:
                raise ValueError("Content type not supported.")

            logger.info(f"File saved locally: {file_path}")

        except Exception as e:
            failed_saves.append({"file_name": file_name, "error": str(e)})

    if len(failed_saves) > 0:
        raise Exception(f"Error saving the following files: \n{failed_saves}")


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
