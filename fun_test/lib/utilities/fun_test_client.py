#!/usr/bin/env python
import os
import json
import sys
import requests
import json
import time
import logging
# import urllib2
logging.basicConfig(level=logging.INFO)



print "my remote Script"
print json.dumps(os.environ.__dict__, indent=4)
print "sys.argv: {}".format(sys.argv)
print "End my remote script"

LOG_FILE = "fun_test_client.log.html"
default_to_addresses = ["john.abraham@fungible.com"]
POLL_INTERVAL = 10
BASE_URL = "http://127.0.0.1:5000"
# BASE_URL = "http://qa-ubuntu-01"

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
        self._write_html(content)


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
        print resp.elapsed.total_seconds()
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

    def submit_job(self, suite_path, build_url, tags=[]):
        suite_execution_id = None
        job_spec = {}
        job_spec["suite_path"] = suite_path
        job_spec["build_url"] = build_url
        job_spec["tags"] = tags
        response = self._do_post(url="/regression/submit_job", data=json.dumps(job_spec))
        if response["status"]:
            suite_execution_id = int(response["data"])
        else:
            error_message = "Failed to submit_job: {} response: {}".format(suite_path, json.dumps(response))
            self.report_error(error_message, suite_path)
        return suite_execution_id

    def get_suite_status(self, suite_execution_id):
        suite_result = "UNKNOWN"
        response = self._do_get(url="/regression/suite_execution/" + str(suite_execution_id))
        if response["status"]:
            suite_result = json.loads(response["data"])
        else:
            error_message = "Unable to fetch suite status of {}".format(suite_execution_id)
            self.report_error(error_message, "")
        return suite_result

    def _write_html(self, contents):
        f = open(LOG_FILE, "a+")
        f.write(contents)
        f.close()

    def get_job_status(self, job_id):
        response = self._do_get(url="/scheduler/get_job_status/" + job_id)
        return response

if __name__ == "__main__":
    fun_test_client = FunTestClient(base_url=BASE_URL)
    suite_execution_id = fun_test_client.submit_job(suite_path="test2.json", build_url="http://dochub.fungible.local/doc/jenkins/funsdk/latest/")
    suite_result = "UNKNOWN"
    while (suite_result == "UNKNOWN") or (suite_result == "IN_PROGRESS") or (suite_result == "QUEUED"):
        suite_result = fun_test_client.get_suite_status(suite_execution_id=suite_execution_id)["suite_result"]
        time.sleep(POLL_INTERVAL)
        logging.info("Suite-result: {}".format(suite_result))
    print "Suite Result: {}".format(suite_result)