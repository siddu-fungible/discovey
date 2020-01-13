from lib.system.fun_test import fun_test
from fun_settings import TESTRAIL_URL
import requests
import requests.auth
import json


class TestRailApi:
    base_url = TESTRAIL_URL

    def __init__(self, project_name):
        self.http_basic_auth = requests.auth.HTTPBasicAuth(username="john.abraham@fungible.com", password="fun123")
        project = self.get_project_by_name(name=project_name)
        self.project_id = project["id"]

    def get(self, url):
        response = requests.get(url, auth=self.http_basic_auth, headers={"Content-type": "application/json"})
        return response.json()

    def get_projects(self):
        url = self.base_url + "?/api/v2/get_projects"
        projects = self.get(url=url)
        return projects

    def get_project_by_name(self, name):
        projects = self.get_projects()
        result = None
        for project in projects:
            if name == project["name"]:
                result = project
                break
        return result

    def get_suites(self):
        url = self.base_url + "?/api/v2/get_suites/{}".format(self.project_id)
        return self.get(url=url)

    def get_cases(self):
        suites = self.get_suites()
        suite_ids = [x["id"] for x in suites]
        all_cases = []
        for suite_id in suite_ids:
            url = self.base_url + "?/api/v2/get_cases/{}&suite_id={}".format(self.project_id, suite_id)
            cases = self.get(url=url)
            all_cases.extend(cases)
        return all_cases

if __name__ == "__main__":
    tr = TestRailApi(project_name="Experimental")
    print json.dumps(tr.get_cases(), indent=4)