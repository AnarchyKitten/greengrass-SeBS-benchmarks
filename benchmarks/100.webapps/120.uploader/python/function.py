import json
from time import sleep
import logging
import platform
import sys
from threading import Timer

import datetime
import os
import uuid

import urllib.request

from . import storage
storage_client = storage.storage.get_instance()

import greengrasssdk

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

# Retrieving platform information to send from the Lambda function - Greengrass_HelloWorld_Bd7Ah
my_platform = platform.platform()

import greengrasssdk

def lambda_handler(event, context):

    output_bucket = event.get('bucket').get('output')
    url = event.get('object').get('url')
    name = os.path.basename(url)
    download_path = '/tmp/{}'.format(name)

    process_begin = datetime.datetime.now()
    urllib.request.urlretrieve(url, filename=download_path)
    size = os.path.getsize(download_path)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    key_name = client.upload(output_bucket, name, download_path)
    upload_end = datetime.datetime.now()

    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    
    # Publish the response to MQTT if got invoked
    try:
        if not my_platform:
            client.publish(
                topic="hello/world", queueFullPolicy="AllOrException", payload="Hello world! Sent from the Lambda function - SeBS-01-Sleep."
            )
        else:
            client.publish(
                topic="hello/world",
                queueFullPolicy="AllOrException",
                payload="Hello world! Sent from " "the Lambda function - SeBS-01-Sleep running on platform: {}".format(my_platform),
            )
    except Exception as e:
        logger.error("Failed to publish message: " + repr(e))

    return {
            'result': {
                'bucket': output_bucket,
                'url': url,
                'key': key_name
            },
            'measurement': {
                'download_time': 0,
                'download_size': 0,
                'upload_time': upload_time,
                'upload_size': size,
                'compute_time': process_time
            }
    }


import datetime
import os
import uuid

import urllib.request

from . import storage
client = storage.storage.get_instance()


def handler(event):
  
    output_bucket = event.get('bucket').get('output')
    url = event.get('object').get('url')
    name = os.path.basename(url)
    download_path = '/tmp/{}'.format(name)

    process_begin = datetime.datetime.now()
    urllib.request.urlretrieve(url, filename=download_path)
    size = os.path.getsize(download_path)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    key_name = storage_client.upload(output_bucket, name, download_path)
    upload_end = datetime.datetime.now()

    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {
                'bucket': output_bucket,
                'url': url,
                'key': key_name
            },
            'measurement': {
                'download_time': 0,
                'download_size': 0,
                'upload_time': upload_time,
                'upload_size': size,
                'compute_time': process_time
            }
    }
