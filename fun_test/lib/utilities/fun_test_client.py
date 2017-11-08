import requests
import json
import time
# logging.basicConfig(level=logging.DEBUG)
# httplib.HTTPConnection.debuglevel = 1s

LOG_FILE = "fun_test_client.log.html"


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
        self.cookies = {}

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
        from_address = "john.abraham@fungible.com"

        subject = "FunTest Interface error:" + error_message
        content = "Suite: %s" % (suite_name) + " Error:" + error_message + " seen"
        # send_mail(from_address=from_address, to_addresses=default_to_addresses, subject=subject, content=content)


    def _do_get(self, url):
        self.cookies['sessionid'] = self.session_id
        resp = requests.get(url=self.base_url + url,
                            cookies=self.cookies,
                            headers={"X-CSRFToken": self.csrf_token})

        response_json = None
        try:
            response_json = json.loads(resp.text)
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

    def submit_job(self, suite_path, build_url):
        job_spec = {}
        job_spec["suite_path"] = suite_path
        job_spec["build_url"] = build_url
        response = self._do_post(url="/regression/submit_job", data=json.dumps(job_spec))
        return response

    def get_suite_status(self, suite_execution_id):
        return self._do_get(url="/regression/suite_execution/" + str(suite_execution_id))

    def _write_html(self, contents):
        f = open(LOG_FILE, "a+")
        f.write(contents)
        f.close()

    def get_job_status(self, job_id):
        response = self._do_get(url="/scheduler/get_job_status/" + job_id)
        return response

if __name__ == "__main__":
    '''
    suites = {
        "suite_name": "storage_sanity.json",
        "build_url": "http://dochub.fungible.local/doc/jenkins/funos/940/"
    }'''
    fun_test_client = FunTestClient(base_url='http://127.0.0.1:5000')
    suite_execution_id = fun_test_client.submit_job(suite_path="storage_basic", build_url="http://dochub.fungible.local/doc/jenkins/funos/940/")
    suite_result = "UNKNOWN"
    while (suite_result == "UNKNOWN") or (suite_result == "IN_PROGRESS"):
        result = fun_test_client.get_suite_status(suite_execution_id=suite_execution_id)
        suite_result = result["suite_result"]
        time.sleep(5)
    print "Suite Result: {}".format(suite_result)