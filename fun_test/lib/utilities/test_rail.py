from lib.system.fun_test import fun_test
from fun_settings import TESTRAIL_URL
import requests
import requests.auth
import json


class TestRailApi:
    class Result:
        PASSED = 1
        BLOCKED = 2
        UNTESTED = 3
        RETEST = 4
        FAILED = 5

    base_url = TESTRAIL_URL

    def __init__(self, project_name, run_name):
        self.http_basic_auth = requests.auth.HTTPBasicAuth(username="john.abraham@fungible.com", password="fun123")
        project = self.get_project_by_name(name=project_name)
        self.project_id = project["id"]
        self.run_name = run_name

    def get(self, url):
        response = requests.get(url, auth=self.http_basic_auth, headers={"Content-type": "application/json"})
        return response.json()

    def post(self, url, payload):
        response = requests.post(url, payload, auth=self.http_basic_auth, headers={"Content-type": "application/json"})
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

    def get_runs(self):
        url = self.base_url + "?/api/v2/get_runs/{}".format(self.project_id)
        return self.get(url)

    def get_run(self, run_name):
        result = None
        runs = self.get_runs()
        for run in runs:
            if run_name == run["name"]:
                result = run
                break
        return result

    def get_run_id(self, run_name):
        run = self.get_run(run_name=run_name)
        result = None
        if run:
            result = run["id"]
        return result

    def get_tests(self, run_name):
        run_id = self.get_run_id(run_name=run_name)
        result = None
        if run_id:
            url = self.base_url + "?/api/v2/get_tests/{}".format(run_id)
            result = self.get(url=url)
        return result

    def get_test_by_case_id(self, case_id):
        tests = self.get_tests(run_name=self.run_name)
        result = None
        for test in tests:
            if test["case_id"] == int(case_id.lstrip("C")):
                result = test
                break
        return result

    def set_result(self, case_id, result_to_set):
        test = self.get_test_by_case_id(case_id=case_id)
        if test:
            test_id = test["id"]
            url = self.base_url + "?/api/v2/add_result/{}".format(test_id)
            payload = {"status_id": result_to_set}
            response = self.post(url, json.dumps(payload))
            print json.dumps(response, indent=4)

if __name__ == "__main__":
    tr = TestRailApi(project_name="Experimental", run_name="AARun")
    # print json.dumps(tr.get_cases(), indent=4)
    # print json.dumps(tr.get_runs(), indent=4)
    # print json.dumps(tr.get_run(run_name="AARun"), indent=4)
    # print json.dumps(tr.get_tests(run_name="AARun"), indent=4)
    # print json.dumps(tr.get_test_by_case_id(case_id="C19879"), indent=4)

    tr.set_result(case_id="C19879", result_to_set=TestRailApi.Result.FAILED)
