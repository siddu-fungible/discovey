from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from scheduler.mq_broker_global import BrokerMessageTypes
import pika
import json


@csrf_exempt
@api_safe_json_response
def publish(request):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        if channel:
            message_type = request_json.get("message_type", None)
            message = request_json.get("message", None)
            routing_key = request_json.get("routing_key", None)
            body = {"message_type": message_type, "message": message}
            channel.basic_publish(exchange='', routing_key=routing_key, body=json.dumps(body))
            connection.close()
            result = True
    return result


@api_safe_json_response
def message_types(request):
    result = BrokerMessageTypes().all_strings_to_code()
    return result
