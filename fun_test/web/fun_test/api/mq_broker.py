from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
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

        channel.basic_publish(exchange='', routing_key=request_json["routing_key"], body='Hello World!')
        connection.close()
    return result
