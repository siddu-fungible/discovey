import requests
import json
import time
# logging.basicConfig(level=logging.DEBUG)
# httplib.HTTPConnection.debuglevel = 1s

LOG_FILE = "saf_client.log.html"


default_to_addresses = ["john.abraham@fungible.com"]


class FunTestClient:
    STATUS_UNKNOWN = "UNKNOWN"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_QUEUED = "QUEUED"
    DEBUG = True

    def __init__(self, base_url):
        self.base_url = base_url
        self.session_id = None
        self.csrf_token = None

    def _connect(self):
        result = False
        if self.session_id:
            return True
        try:
            resp = requests.get(self.base_url)
            self.cookies = resp.cookies
            self.csrf_token = self.cookies['csrftoken']
            result = True
        except Exception as ex:
            print(ex.message)
        return result

    def report_error(self, error_message, suite_name):
        from_address = "TA_Server@scalearc.com"

        subject = "FunTest Interface error:" + error_message
        content = "Suite: %s" % (suite_name) + " Error:" + error_message + " seen"
        # send_mail(from_address=from_address, to_addresses=default_to_addresses, subject=subject, content=content)

    def login(self, username='root', password='r00t.!@#'):
        result = False
        self._connect()
        if self.csrf_token:
            resp = requests.post(self.base_url + '/accounts/login/',
                                 data={"username": username,
                                       "password": password,
                                       "csrfmiddlewaretoken": self.csrf_token},
                                 cookies=self.cookies, allow_redirects=False)
            self.session_id = resp.cookies['sessionid']
            result = True
        else:
            result = False
        return result

    def _do_get(self, url):
        self.cookies['sessionid'] = self.session_id
        resp = requests.get(url=self.base_url + url,
                            cookies=self.cookies,
                            headers={"X-CSRFToken": self.csrf_token})

        response_json = None
        try:
            response_json = json.loads(resp.text)
            self._print_json(d=response_json)
            total_tc_count = response_json['total_tc_count']
            pass_tc_count = response_json['pass_tc_count']
            fail_tc_count = response_json['fail_tc_count']
            if (total_tc_count > 0) \
                    and (pass_tc_count > 0) and (total_tc_count == pass_tc_count) and (fail_tc_count == 0):
                response_json['execution_result'] = True
            else:
                response_json['execution_result'] = False
        except Exception as ex:
            print("Exception: " + str(ex))
            self._write_html(contents=resp.text)
        return response_json

    def _do_post(self, url, data):
        self.cookies['sessionid'] = self.session_id
        resp = requests.post(url=self.base_url + url,
                             data=data,
                             cookies=self.cookies,
                             headers={"X-CSRFToken": self.csrf_token})
        response_json = None
        try:
            response_json = json.loads(resp.text)
            self._print_json(d=response_json)
        except:
            self._write_html(contents=resp.text)
        return response_json

    def _print_json(self, d):
        if d and self.DEBUG:
            print(json.dumps(d, indent=4))

    def update_test_result(self, suite_id, qa_engineer, testbed_name, tc_id, test_result):
        self.cookies['sessionid'] = self.session_id
        url = self.base_url + "/scheduler/update_test_result/%d/%s/%s/%s/%d" % (suite_id, qa_engineer, test_result, testbed_name, tc_id)
        resp = requests.get(url=url)
        print resp.text

    def submit_jobs(self, jobs):
        response = self._do_post(url="/scheduler/submit_jobs", data=json.dumps(jobs))
        return response

    def submit_sanity(self, job):
        response = self._do_post(url="/scheduler/submit_sanity", data=json.dumps(job))
        return response['job_id']

    def submit_job_suites(self, suites):
        response = self._do_post(url="/scheduler/submit_job_suites", data=json.dumps(suites))
        return response

    def submit_job_suite(self, suite):
        response = self._do_post(url="/scheduler/submit_job_suite", data=json.dumps(suite))
        return response

    def get_master_suite_status(self, master_suite_id):
        master_suite_status = "Failed"
        suite_ids = self._do_get(url="/scheduler/get_suites_for_master/" + str(master_suite_id))

        all_completed = True
        any_running = False
        any_submitted = False
        for suite_id in suite_ids:
            suite_status = self.get_suite_status(suite_id=suite_id)['status']
            if suite_status != "Completed":
                all_completed = False
            if suite_status == "Pending" or (suite_status == "Running"):
                any_running = True
                break
            if suite_status == "Submitted":
                any_submitted = True
        if all_completed:
            master_suite_status = "Completed"
        if any_submitted:
            master_suite_status = "Submitted"
        if any_running:
            master_suite_status = "Running"
        return master_suite_status

    def get_suite_results(self, master_suite_id):
        suite_results = {}
        try:
            suite_ids = self._do_get(url="/scheduler/get_suites_for_master/" + str(master_suite_id))
            for suite_id in suite_ids:
                response = self.get_suite_status(suite_id=suite_id)
                suite_status = response['status']
                jira_id = response['jira_id']
                result_url = response['result_url']
                suite_results[jira_id] = {'status': suite_status, "result_url": result_url}

        except Exception as ex:
            print(str(ex))
        return suite_results


    def get_suite_status(self, suite_id):
        return self._do_get(url="/scheduler/get_suite_status/" + str(suite_id))

    def _write_html(self, contents):
        f = open(LOG_FILE, "a+")
        f.write(contents)
        f.close()

    def add_testcases_by_jql(self, jira_id, jql_str):
        test_case = {}
        test_case["test_components"] = []
        test_case["test_sub_component"] = []
        test_case["db_type"] = "MSSQL"
        test_case["jql_str"] = jql_str
        test_case["sql_server_version"] = ["2014"]
        response = self._do_post(url="/scheduler/create_test_suite/" + jira_id, data=json.dumps(test_case))
        return response

    def get_job_status(self, job_id):
        response = self._do_get(url="/scheduler/get_job_status/" + job_id)
        return response

if __name__ == "__main__":
    suites = {
        "suite_name"
    }
    saf_client = SafClient(base_url='http://172.20.9.39:5000')
    if saf_client.login(username='root', password='r00t.!@#'):
        submission_response = saf_client.submit_job_suites(suites=suites)
        master_suite_id = submission_response["master_suite_id"]
        print("Master Suite-Id: %d" % (master_suite_id))
        master_suite_submission_status = submission_response["status"]

        if master_suite_submission_status != "Failed":
            print("Master Suite-status: %s" % (master_suite_submission_status))
            suite_results = saf_client.get_suite_results(master_suite_id=master_suite_id)
            print("****")
            for jira_id, info in suite_results.items():
                print("IDB-%s: Status: %s Url:%s" % (jira_id, info['status'], info['result_url']))

            status = saf_client.get_master_suite_status(master_suite_id=master_suite_id)
            if not status == "Failed":
                while status != "Completed":
                    time.sleep(5)
                    status = saf_client.get_master_suite_status(master_suite_id=master_suite_id)
                    print("Current Status:" + status)
        else:
            print("*** Suite submission failed ***\n")
            print(json.dumps(master_suite_submission_status, indent=4))
            raise Exception("Suite submission failed: %s" % (master_suite_submission_status["error_message"]))
    else:
        raise Exception("Login failed")