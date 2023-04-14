import logging
import datetime, io, json
# using https://squiggle.readthedocs.io/en/latest/
from squiggle import transform

from . import storage
storage_client = storage.storage.get_instance()

import greengrasssdk
# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

lambda_name = "SeBS-502-Graph-mst"
result_mqtt_topic = "result/graph-mst"

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

def lambda_handler(event, context):

    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = event.get('object').get('key')
    download_path = '/tmp/{}'.format(key)

    download_begin = datetime.datetime.now()
    storage_client.download(input_bucket, key, download_path)
    download_stop = datetime.datetime.now()
    data = open(download_path, "r").read()

    process_begin = datetime.datetime.now()
    result = transform(data)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    buf = io.BytesIO(json.dumps(result).encode())
    buf.seek(0)
    key_name = storage_client.upload_stream(output_bucket, key, buf)
    upload_stop = datetime.datetime.now()
    buf.close()

    download_time = (download_stop - download_begin) / datetime.timedelta(microseconds=1)
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
                'compute_time': process_time
            }
    }
