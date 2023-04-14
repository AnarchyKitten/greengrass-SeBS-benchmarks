import json
import logging
import datetime
import io
import os
import shutil
import uuid
import zlib

import greengrasssdk

from . import storage
storage_client = storage.storage.get_instance()

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

lambda_name = "SeBS-311-Compression"
result_mqtt_topic = "result/compression"

def send_mqtt_response(topic, lambdaName, resultPayload):
    # Publish the response to MQTT if got invoked
    try:
        client.publish(
            topic=topic,
            queueFullPolicy="AllOrException",
            payload="Lambda function - {} succeeded with result {} .".format(lambdaName, resultPayload),
        )
    except Exception as e:
        logger.error("Failed to publish message: " + repr(e))

def parse_directory(directory):

    size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            size += os.path.getsize(os.path.join(root, file))
    return size

def lambda_handler(event, context):
  
    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = event.get('object').get('key')
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())
    os.makedirs(download_path)

    s3_download_begin = datetime.datetime.now()
    storage_client.download_directory(input_bucket, key, download_path)
    s3_download_stop = datetime.datetime.now()
    size = parse_directory(download_path)

    compress_begin = datetime.datetime.now()
    shutil.make_archive(os.path.join(download_path, key), 'zip', root_dir=download_path)
    compress_end = datetime.datetime.now()

    s3_upload_begin = datetime.datetime.now()
    archive_name = '{}.zip'.format(key)
    archive_size = os.path.getsize(os.path.join(download_path, archive_name))
    key_name = storage_client.upload(output_bucket, archive_name, os.path.join(download_path, archive_name))
    s3_upload_stop = datetime.datetime.now()

    download_time = (s3_download_stop - s3_download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (s3_upload_stop - s3_upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (compress_end - compress_begin) / datetime.timedelta(microseconds=1)
    
    # TODO: add return result payload
    result_payload = "{'result': }"
    
    # Publish the response to MQTT if got invoked
    send_mqtt_response(result_mqtt_topic, lambda_name, result_payload)

    
    return {
            'result': {
                'bucket': output_bucket,
                'key': key_name
            },
            'measurement': {
                'download_time': download_time,
                'download_size': size,
                'upload_time': upload_time,
                'upload_size': archive_size,
                'compute_time': process_time
            }
        }

