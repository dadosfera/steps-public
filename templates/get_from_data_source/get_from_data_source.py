import boto3
from typing import Dict, Union
import os
import sys
import json
from dadosfera.services.s3 import list_s3_objects
import logging
import chardet

ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_from_data_source():
    """Define the function that should be executed"""


def orchest_handler():
    import orchest

    output_variable = orchest.get_step_param("output_variable")
    objects = get_from_data_source()
    orchest.output(data=objects, name=output_variable)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    output_filepath = config.get("output_filepath")
    objects = get_from_data_source()

    with open(output_filepath, "w") as f:
        f.write(json.dumps(objects))


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
