import json
import logging
import datetime
import io
import os
import sys
import uuid
from urllib.parse import unquote_plus
from PIL import Image

import greengrasssdk

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

lambda_name = "SeBS-210-Thumbnailer"
result_mqtt_topic = "result/thumbnailer"

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
    

from . import storage
storage_client = storage.storage.get_instance()

# Disk-based solution
#def resize_image(image_path, resized_path, w, h):
#    with Image.open(image_path) as image:
#        image.thumbnail((w,h))
#        image.save(resized_path)

# Memory-based solution
def resize_image(image_bytes, w, h):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.thumbnail((w,h))
        out = io.BytesIO()
        image.save(out, format='jpeg')
        # necessary to rewind to the beginning of the buffer
        out.seek(0)
        return out

def lambda_handler(event, context):
  
    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = unquote_plus(event.get('object').get('key'))
    width = event.get('object').get('width')
    height = event.get('object').get('height')
    # UUID to handle multiple calls
    #download_path = '/tmp/{}-{}'.format(uuid.uuid4(), key)
    #upload_path = '/tmp/resized-{}'.format(key)
    #storage_client.download(input_bucket, key, download_path)
    #resize_image(download_path, upload_path, width, height)
    #storage_client.upload(output_bucket, key, upload_path)
    download_begin = datetime.datetime.now()
    img = storage_client.download_stream(input_bucket, key)
    download_end = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    resized = resize_image(img, width, height)
    resized_size = resized.getbuffer().nbytes
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    key_name = storage_client.upload_stream(output_bucket, key, resized)
    upload_end = datetime.datetime.now()

    download_time = (download_end - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)

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
                'download_size': len(img),
                'upload_time': upload_time,
                'upload_size': resized_size,
                'compute_time': process_time
            }
    }
