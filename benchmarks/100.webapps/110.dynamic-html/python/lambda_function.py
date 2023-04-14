import json
import logging
import sys
from datetime import datetime                                                   
from random import sample  
from os import path
from time import time                                                           
import os

import greengrasssdk

from jinja2 import Template

SCRIPT_DIR = path.abspath(path.join(path.dirname(__file__)))

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

lambda_name = "SeBS-110-Dynamic-html"
result_mqtt_topic = "result/dynamic-html"

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

    # start timing
    name = event.get('username')
    size = event.get('random_len')
    cur_time = datetime.now()
    random_numbers = sample(range(0, 1000000), size)
    template = Template(open(path.join(SCRIPT_DIR, 'templates', 'template.html'), 'r').read())
    html = template.render(username = name, cur_time = cur_time, random_numbers = random_numbers)
    # end timing

    # TODO: add return result payload
    result_payload = "{'result': }"
    
    # Publish the response to MQTT if got invoked
    send_mqtt_response(result_mqtt_topic, lambda_name, result_payload)

    # dump stats 
    return {'result': html}