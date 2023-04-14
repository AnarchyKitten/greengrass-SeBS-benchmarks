import logging
import datetime, json, os, uuid

from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet50

import greengrasssdk

from . import storage
storage_client = storage.storage.get_instance()

SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
class_idx = json.load(open(os.path.join(SCRIPT_DIR, "imagenet_class_index.json"), 'r'))
idx2label = [class_idx[str(k)][1] for k in range(len(class_idx))]
model = None

# Setup logging to stdout
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Creating a greengrass core sdk client
client = greengrasssdk.client("iot-data")

lambda_name = "SeBS-411-Image-Recognition"
result_mqtt_topic = "result/image-recognition"

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
  
    model_bucket = event.get('bucket').get('model')
    input_bucket = event.get('bucket').get('input')
    key = event.get('object').get('input')
    model_key = event.get('object').get('model')
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())

    image_download_begin = datetime.datetime.now()
    image_path = download_path
    storage_client.download(input_bucket, key, download_path)
    image_download_end = datetime.datetime.now()

    global model
    if not model:
        model_download_begin = datetime.datetime.now()
        model_path = os.path.join('/tmp', model_key)
        storage_client.download(model_bucket, model_key, model_path)
        model_download_end = datetime.datetime.now()
        model_process_begin = datetime.datetime.now()
        model = resnet50(pretrained=False)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        model_process_end = datetime.datetime.now()
    else:
        model_download_begin = datetime.datetime.now()
        model_download_end = model_download_begin
        model_process_begin = datetime.datetime.now()
        model_process_end = model_process_begin
   
    process_begin = datetime.datetime.now()
    input_image = Image.open(image_path)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model 
    output = model(input_batch)
    _, index = torch.max(output, 1)
    # The output has unnormalized scores. To get probabilities, you can run a softmax on it.
    prob = torch.nn.functional.softmax(output[0], dim=0)
    _, indices = torch.sort(output, descending = True)
    ret = idx2label[index]
    process_end = datetime.datetime.now()

    download_time = (image_download_end- image_download_begin) / datetime.timedelta(microseconds=1)
    model_download_time = (model_download_end - model_download_begin) / datetime.timedelta(microseconds=1)
    model_process_time = (model_process_end - model_process_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    
    # TODO: add return result payload
    result_payload = "{'result': }"
    
    # Publish the response to MQTT if got invoked
    send_mqtt_response(result_mqtt_topic, lambda_name, result_payload)
    
    return {
            'result': {'idx': index.item(), 'class': ret},
            'measurement': {
                'download_time': download_time + model_download_time,
                'compute_time': process_time + model_process_time,
                'model_time': model_process_time,
                'model_download_time': model_download_time
            }
        }

