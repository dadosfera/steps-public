from dadosfera.services.scraping import extract_text_from_html
import os
import sys
import json
import logging
from typing import List, Dict

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def apply_transformation(objects: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Define the transformation that will be applied in the data"""

def orchest_handler():
    import orchest
    incoming_variable_name = orchest.get_step_param('incoming_variable_name')
    output_variable_name = orchest.get_step_param('output_variable_name')
    inputs = orchest.get_inputs()[incoming_variable_name]
    objects = apply_transformation(inputs)
    orchest.output(data=objects, name=output_variable_name)


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    input_filepath = config.get('input_filepath')
    output_filepath = config.get('output_filepath')

    with open(input_filepath,'r') as f:
        objects = json.loads(f.read())

    objects = apply_transformation(objects)

    with open(output_filepath,'w') as f:
        objects = f.write(json.dumps(objects))



if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info('Running as orchest Step')
        orchest_handler()
    else:
        script_handler()
        logger.info('Running as script')
