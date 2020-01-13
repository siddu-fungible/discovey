from fun_settings import TESTRAIL_URL
import requests
import requests.auth
import json

class TestRailApi:
    base_url = TESTRAIL_URL

    def __init__(self):
        self.http_basic_auth = requests.auth.HTTPBasicAuth(username="john.abraham@fungible.com", password="fun123")

    def something(self):
        pass


    def get(self, url):
        response = requests.get(url, auth=self.http_basic_auth, headers={"Content-type": "application/json"})
        return response.json()

    def get_projects(self):
        url = self.base_url + "?/api/v2/get_projects"
        projects = self.get(url=url)
        return projects


if __name__ == "__main__":
    print json.dumps(TestRailApi().get_projects(), indent=4)
