import django_interactive
from django.test import Client
import json

class TestClient():
    def __init__(self):
        self.client = Client()


    def post(self, url, payload):
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        return json.loads(response.content)

    def get(self, url):
        response = self.client.get(url, content_type='application/json')
        return json.loads(response.content)



if __name__ == "__main__":
    client = TestClient()

    '''
    url = "/regression/script"
    payload = {"script_path": "/networking/vp/test_sanity_vp_path_random.py"}
    response = client.post(url, payload)
    pk = response['data']['pk']

    payload = {"suite_execution_id": 5089}
    url = "/regression/script_execution/" + str(pk)
    response = client.post(url, payload)

    print response
    '''
    base_url = "integration.fungible.local"
    url = base_url + "/regression/get_test_case_executions_by_time"
    payload = {"test_case_execution_tags": ["palladium-apps"]}
    response = client.post(url, payload)
    print response
