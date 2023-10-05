import boto3
import json
import sys
import os
import logging
from typing import Dict, Union, List

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def put_in_target_location(objects: List[Dict[str, str]]):
    """Define your function that ingest data into a location"""

def orchest_handler():
    import orchest
    incoming_variable_name = orchest.get_step_param('incoming_variable_name')

    objects = orchest.get_inputs()[incoming_variable_name]
    put_in_target_location(objects=objects)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    input_filepath = config['input_filepath']
    with open(input_filepath,'r') as f:
        objects = json.load(f)

    put_in_target_location(objects=objects)

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
