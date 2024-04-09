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

def put_objects_in_s3(
    objects: List[str],
    bucket_name: str,
    prefix: str,
    file_extension: str
) -> Union[Dict[str, str], None]:
    client = boto3.client('s3', region_name='us-east-1')


    failed_uploads = []

    logger.info(f'There are {len(objects)} to be uploaded')
    for object_ in objects:

        if file_extension is not None:
            key = f"{prefix}/{object_['file_name']}.{file_extension}"
        else:
            key = f"{prefix}/{object_['file_name']}"
        logger.debug(f'Putting object {key} in s3')


        if isinstance(object_['file_content'], str):
            object_['file_content'] = object_['file_content'].encode('utf-8')

        response = client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=object_['file_content']
        )


        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            failed_uploads.append({'object_metadata': object_['file_name'], 'boto_response': response['ResponseMetadata']})


    if len(failed_uploads) > 0:
        raise Exception(f"Failed to upload the following files: \n{failed_uploads}")

def orchest_handler():
    import orchest
    bucket_name = orchest.get_step_param('bucket_name')
    prefix = orchest.get_step_param('prefix')
    file_extension = orchest.get_step_param('file_extension')
    input_type = orchest.get_step_param('input_type')


    if prefix is None:
        prefix = ''

    if input_type == "from_filepath":
        input_filepaths = orchest.get_step_param("input_filepaths")

        objects = []
        for input_filepath in input_filepaths:
            with open(input_filepath) as f:
                file_content = json.loads(f.read())
            objects.append({
                "file_name": input_filepath,
                "file_content": file_content
            })

    elif input_type == "from_incoming_variable":
        incoming_variable_name = orchest.get_step_param("incoming_variable_name")
        objects = orchest.get_inputs()[incoming_variable_name]

    put_objects_in_s3(
        objects=objects,
        bucket_name=bucket_name,
        prefix=prefix,
        file_extension=file_extension
    )

def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")
    config_json = sys.argv[1]
    config = json.loads(config_json)

    input_filepath = config['input_filepath']
    bucket_name = config['bucket_name']
    prefix = config.get('prefix')

    if prefix is None:
        prefix = ''

    file_extension = config.get('file_extension')

    with open(input_filepath,'r') as f:
        objects = json.load(f)

    put_objects_in_s3(
        objects=objects,
        bucket_name=bucket_name,
        prefix=prefix,
        file_extension=file_extension
    )

if __name__ == "__main__":

    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
