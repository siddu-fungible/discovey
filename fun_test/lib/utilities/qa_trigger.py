#!/usr/bin/env python2.7
"""
Script that triggers and monitors job on Integration team server.
"""
import os
import sys
import argparse
import json
import time
import logging
import httplib
import time

logging.basicConfig(level=logging.INFO)

LOG_FILE = "fun_test_client.log.html"
DEFAULT_BUILD_URL = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/"
#  Won't be used, but the fun_test API needs some default

DEFAULT_POLL_INTERVAL_SECONDS = 60
DEFAULT_BASE_URL = "http://integration.fungible.local"
DEFAULT_SUBMITTER_EMAIL = "team-regression@fungible.com"

TIME_OUT_EXIT_CODE = -999
PASSED_EXIT_CODE = 0
FAILED_EXIT_CODE = -1
GENERIC_ERROR_EXIT_CODE = -111


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

    def report_error(self, error_message, suite_name):
        from_address = "john.abraham@fungible.com"
        subject = "FunTest Interface error: %s" % error_message
        content = "Suite: %s, Error: %s" % (suite_name, error_message)
        # send_mail(from_address=from_address, to_addresses=default_to_addresses, subject=subject, content=content)
        self._write_html(content)

    def _http_connection(self):
        base_url = self.base_url
        http_prefix = "http://"
        if base_url.startswith(http_prefix):
            base_url = base_url[len(http_prefix):]
        return httplib.HTTPConnection(base_url)

    def _do_get(self, url):
        self.cookies['sessionid'] = self.session_id
        """
        resp = requests.get(url=self.base_url + url,
                            cookies=self.cookies,
                            headers={"X-CSRFToken": self.csrf_token})
        """
        logging.info("GET {}".format(url))

        conn = self._http_connection()
        conn.request("GET", url, None, {"X-CSRFToken": self.csrf_token})
        response = conn.getresponse()
        response_json = None
        try:
            if response.status == 200:
                data = response.read()
                response_json = json.loads(data)
                self._print_json(d=response_json)
            else:
                raise Exception("GET: {} Failed".format(url))
        except Exception as ex:
            error_message = "GET: ex: {} HTTP: status: {}, reason: {}".format(
                str(ex), response.status, response.reason)
            self._write_html(contents=error_message)
        return response_json

    def _do_post(self, url, data):
        self.cookies['sessionid'] = self.session_id
        """
        resp = requests.post(url=self.base_url + url,
                             data=data,
                             cookies=self.cookies,
                             headers={"X-CSRFToken": self.csrf_token})
        """
        logging.info("POST {}".format(url))
        self._print_json(d=json.loads(data))
        # self._print_json(data)

        conn = self._http_connection()
        conn.request("POST", url, data, {"X-CSRFToken": self.csrf_token})
        response = conn.getresponse()
        response_json = None
        try:
            if response.status == 200:
                data = response.read()
                response_json = json.loads(data)
                self._print_json(d=response_json)
            else:
                raise Exception("POST: {} Failed".format(url))
        except Exception as ex:
            error_message = "POST: ex: {} HTTP: status: {}, reason: {}".format(
                str(ex), response.status, response.reason)
            self._write_html(contents=error_message)
        return response_json

    def _print_json(self, d):
        if d and self.DEBUG:
            logging.info(json.dumps(d, indent=4))

    def submit_job(self,
                   suite_path,
                   build_url,
                   submitter_email=None,
                   tags=None,
                   email_list=None,
                   environment=None,
                   test_bed_type="emulation",
                   description=""):
        if not tags:
            tags = []
        elif isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",")]

        if not email_list:
            email_list = []
        elif isinstance(email_list, str):
            email_list = [email.strip() for email in email_list.split(",")]

        suite_execution_id = None
        job_spec = {
            "suite_path": suite_path,
            "build_url": build_url,
            "tags": tags,
            "email_list": email_list,
            "submitter_email": submitter_email,
            "environment": environment,
            "test_bed_type": test_bed_type,
            "description": description
        }
        response = self._do_post(url="/regression/submit_job", data=json.dumps(job_spec))
        if response["status"]:
            suite_execution_id = int(response["data"])
        else:
            error_message = "Failed to submit_job: {} response: {}".format(suite_path, json.dumps(response))
            self.report_error(error_message, suite_path)
        return suite_execution_id

    def _write_html(self, contents):
        with open(LOG_FILE, "a+") as f:
            f.write(contents)

    def get_job_status(self, job_id):
        response = self._do_get(url="/api/v1/regression/suite_executions/{}?is_job_completed=true".format(job_id))
        return response



def main():
    exit_code = 0
    parser = argparse.ArgumentParser(description='Trigger and monitor job on Integration team server')
    parser.add_argument('--suite_name', help='Suite name', required=True)
    parser.add_argument('--emails', help='Email addresses', required=True)
    parser.add_argument('--tags', help='Tags')
    parser.add_argument('--base_url', help="Base URL")
    parser.add_argument('--submitter_email', help="Submitter's email address", default=DEFAULT_SUBMITTER_EMAIL)
    parser.add_argument('--environment', help="Custom environment")
    parser.add_argument('--max_run_time', help="Max run-time", default=60 * 60 * 3)
    parser.add_argument('--test_bed_type', default="fs-6", help="emulation or simulation or fs")
    parser.add_argument('--description', default="Unknown description")
    args = parser.parse_args()

    suite_name = args.suite_name
    emails = args.emails
    submitter_email = args.submitter_email
    tags = args.tags
    base_url = args.base_url
    environment = args.environment
    max_run_time = args.max_run_time
    test_bed_type = args.test_bed_type
    description = args.description

    logging.info("Input options provided:")
    logging.info("Suite        : {}".format(suite_name))
    logging.info("Submitter    : {}".format(submitter_email))
    logging.info("Emails       : {}".format(emails))
    logging.info("Tags         : {}".format(tags))
    logging.info("Base URL     : {}".format(base_url))
    logging.info("Environment  : {}".format(environment))
    logging.info("Test-bed type: {}".format(test_bed_type))
    logging.info("Description  : {}".format(description))
    logging.info("")

    if not base_url:
        base_url = DEFAULT_BASE_URL
        logging.info("No base URL provided")
        logging.info("Using the default base URL:")
        logging.info("Base URL   : {}".format(base_url))
        logging.info("")

    if not environment:
        environment = dict(os.environ)
        logging.info("No custom environment provided")
        logging.info("Using the environment of this script process:")
        logging.info("Environment: {}".format(environment))
        logging.info("")

    poll_interval_seconds = DEFAULT_POLL_INTERVAL_SECONDS

    try:
        fun_test_client = FunTestClient(base_url=base_url)
        start_time = time.time()
        job_id = fun_test_client.submit_job(suite_path=suite_name,
                                            build_url=DEFAULT_BUILD_URL,
                                            tags=tags,
                                            email_list=emails,
                                            environment=environment,
                                            submitter_email=submitter_email,
                                            description=description)

        job_status = None
        if job_id > 0:
            is_job_completed = False
            elapsed_time = 0
            while not is_job_completed and (elapsed_time < max_run_time):
                response = fun_test_client.get_job_status(job_id=job_id)
                if not response["status"]:
                    raise Exception("Invalid job status response: {}".format(json.dumps(response, indent=4)))
                else:
                    job_status = response["data"]
                is_job_completed = job_status["is_completed"]
                if is_job_completed:
                    break

                time.sleep(poll_interval_seconds)
                elapsed_time = time.time() - start_time

            if elapsed_time > max_run_time:
                error_message = "Max run-time: {} seconds exceeded".format(max_run_time)
                logging.error(error_message)
                raise Exception(error_message)

            if is_job_completed:
                logging.info("Job state code: {}".format(job_status["job_state_code"]))
                logging.info("Job state description: {}".format(job_status["job_state_string"]))
                logging.info("Message: {}".format(job_status["message"]))
                logging.info("Result: {}".format(job_status["result"]))

                if job_status["result"] == "PASSED":
                    exit_code = PASSED_EXIT_CODE
                else:
                    exit_code = FAILED_EXIT_CODE
        else:
            logging.exception("Job submission failed.")
    except Exception as ex:
        exit_code = GENERIC_ERROR_EXIT_CODE
        logging.critical("Suite polling ended with exception: {}".format(str(ex)))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
