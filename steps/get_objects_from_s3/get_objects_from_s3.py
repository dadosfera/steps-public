import boto3
from typing import Dict, Union
import os
import sys
import json
from dadosfera.services.s3 import list_s3_objects
import logging
import chardet

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_objects_from_s3(bucket_name: str, prefix: str) -> Union[Dict[str, str], None]:
    client = boto3.client('s3', region_name='us-east-1')

    logger.info(f"Listing objects in bucket {bucket_name} for prefix {prefix}")
    objects_metadata = list_s3_objects(bucket_name=bucket_name, prefix=prefix)
    logger.info(f"Found {len(objects_metadata)} objects")


    objects = []
    for object_metadata in objects_metadata:
        response = client.get_object(Bucket=bucket_name, Key=object_metadata['Key'])
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            body = response['Body'].read()
            objects.append({
                'file_content': body,
                'key': object_metadata['Key'],
                'file_name': object_metadata['Key'].split('/')[-1]
            })

    return objects

def orchest_handler():
    import orchest
    bucket_name = orchest.get_step_param('bucket_name')
    prefix = orchest.get_step_param('prefix')
    output_variable_name = orchest.get_step_param('output_variable_name')
    if prefix is None:
        prefix = ''

    objects = get_objects_from_s3(bucket_name=bucket_name, prefix=prefix)
    orchest.output(data=objects, name=output_variable_name)

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    bucket_name = config.get('bucket_name')
    prefix = config.get('prefix')
    output_filepath = config.get('output_filepath')
    objects = get_objects_from_s3(bucket_name=bucket_name, prefix=prefix)

    with open(output_filepath,'w') as f:
        f.write(json.dumps(objects))


if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
