import json
import logging
import platform
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

# Retrieving platform information to send from the Lambda function
my_platform = platform.platform()

import greengrasssdk

def send_mqtt_response(topic, lambdaName):
    # Publish the response to MQTT if got invoked
    try:
        if not my_platform:
            client.publish(
                topic=topic,
                 queueFullPolicy="AllOrException"
                 , payload="Hello world! Sent from the Lambda function - {}.".format(my_platform),
            )
        else:
            client.publish(
                topic=topic,
                queueFullPolicy="AllOrException",
                payload="Lambda function - {} succeeded on platform: {}".format(lambdaName, my_platform),
            )
    except Exception as e:
        logger.error("Failed to publish message: " + repr(e))
    

def lambda_handler(event, context):

    # start timing
    name = "username"
    size = 500000
    cur_time = datetime.now()
    random_numbers = sample(range(0, 1000000), size)
    template = Template(open(path.join(SCRIPT_DIR, 'templates', 'template.html'), 'r').read())
    html = template.render(username = name, cur_time = cur_time, random_numbers = random_numbers)
    # end timing
    
    # Publish the response to MQTT if got invoked
    send_mqtt_response("result/dynamic-html", "SeBS-110-Dynamic-html")

    # dump stats 
    return {'result': html}