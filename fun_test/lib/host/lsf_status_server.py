from lib.system.fun_test import fun_test
from fun_global import get_localized_time
from fun_settings import JENKINS_USERNAME, JENKINS_PASSWORD
from web.fun_test.models_helper import add_jenkins_job_id_map
import requests
import json
import pytz
from datetime import datetime
from dateutil import parser

LSF_WEB_SERVER_BASE_URL = "http://palladium-jobs.fungible.local:8080"
FUNOS_CONSOLE = "FunOS Console"


class LsfStatusServer:
    def __init__(self):
        self.base_url = LSF_WEB_SERVER_BASE_URL

    def health(self):
        url = "{}".format(self.base_url)
        response = requests.get(url)
        return response.status_code == 200

    def workaround(self, tags):
        try:
            for tag in tags:
                past_jobs = self.get_jobs_by_tag(tag=tag)
                if past_jobs:
                    response_dict = json.loads(past_jobs)
                    # fun_test.log(json.dumps(response_dict, indent=4))
                    past_jobs = response_dict["past_jobs"]
                past_job = past_jobs[0]
                local_past_jobs_index = fun_test.get_local_setting("lsf_past_jobs_index")
                if local_past_jobs_index:
                    past_job = past_jobs[int(local_past_jobs_index)]
                job_id = past_job["job_id"]
                response = self.get_job_by_id(job_id=job_id)
                response = self.get_job_by_id(job_id=job_id)
        except Exception as ex:
            fun_test.critical("Workaround failed:" + str(ex))

    def _get(self, url):
        data = None
        username = JENKINS_USERNAME
        password = JENKINS_PASSWORD
        response = requests.get(url, auth=(username, password))
        if response.status_code == 200:
            data = response.text
        return data

    def get_jobs_by_tag(self, tag):
        url = "{}/?tag={}&format=json".format(self.base_url, tag)
        return self._get(url=url)

    def get_last_job(self, tag, validate=True):
        result = {}
        last_job = {}
        try:
            past_jobs = self.get_past_jobs_by_tag(tag=tag, add_info_to_db=True)
            if len(past_jobs):
                last_job = past_jobs[0]
                local_past_jobs_index = fun_test.get_local_setting("lsf_past_jobs_index")
                if local_past_jobs_index:
                    last_job = past_jobs[int(local_past_jobs_index)]
                job_id = last_job["job_id"]
                jenkins_job_id = last_job["jenkins_build_number"]
                result = last_job
                # result["job_id"] = job_id
                # result["jenkins_build_number"] = jenkins_job_id
                fun_test.add_checkpoint("Validating Job: {}".format(job_id))
                # fun_test.log("Job Info: {}".format(fun_test.dict_to_json_string(last_job)))
                if validate:
                    fun_test.add_checkpoint("Fetching return code for: {}".format(job_id))
                    """
                    response = self.get_job_by_id(job_id=job_id)
                    response = self.get_job_by_id(job_id=job_id)

                
                    response_dict = {"output_text": "-1"}
                    try:
                        response_dict = json.loads(response)
                        # last_job = response_dict
                        response_dict = response_dict["job_dict"]
                        # print(json.dumps(response_dict, indent=4))
                        return_code = int(response_dict["return_code"])
                        # fun_test.test_assert(not return_code, "Valid return code")
                        # result = last_job
                        result["output_text"] = self.get_human_file(job_id=job_id, console_name=FUNOS_CONSOLE)
                    except Exception as ex:
                        fun_test.log("Actual response:" + response)
                        fun_test.critical(str(ex))
                    """
                # last_job = response

                # fun_test.test_assert("output_text" in last_job, "output_text found in job info: {}".format(job_id))

        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_past_jobs_by_tag(self, tag, add_info_to_db=True):
        past_jobs = []
        jobs_by_tag_response = self.get_jobs_by_tag(tag=tag)
        if jobs_by_tag_response:
            response_dict = json.loads(jobs_by_tag_response)
            # fun_test.log(json.dumps(response_dict, indent=4))
            past_jobs = response_dict["past_jobs"]

        if add_info_to_db:
            last_job = past_jobs[0]
            local_past_jobs_index = fun_test.get_local_setting("lsf_past_jobs_index")
            if local_past_jobs_index:
                last_job = past_jobs[int(local_past_jobs_index)]
            for past_job in [last_job]:
                job_dict = past_job
                if "completion_secs" not in job_dict:
                    fun_test.critical("Job: {} has no field named completion_secs".format(job_dict["job_id"]))
                    continue
                completion_date = self.get_completion_date(job_info=job_dict)
                response = ""
                try:
                    response = self.get_job_by_id(job_id=job_dict["job_id"])
                    job_info = json.loads(response)
                    dt = get_localized_time(completion_date)
                    self.add_palladium_job_info(job_dict=job_dict)
                    run_time_properties = self.prepare_run_time_properties(job_dict=job_dict)
                    output_text = self.get_human_file(job_id=job_dict["job_id"], console_name=FUNOS_CONSOLE, job_info=job_info)
                    past_job["date_time"] = dt
                    past_job["output_text"] = output_text
                    past_job["run_time"] = run_time_properties
                except Exception as ex:
                    fun_test.log("Actual response:" + response)
                    fun_test.critical(str(ex))
        return past_jobs

    def get_job_by_id(self, job_id):
        url = "{}/job/{}?format=json".format(self.base_url, job_id)
        return self._get(url=url)

    def get_job_text_by_human_path(self, job_id, log_path):
        url = "{}/job/{}/human_file/{}".format(self.base_url, job_id, log_path)
        return self._get(url=url)

    def get_job_text_by_raw_path(self, job_id, log_path):
        url = "{}/job/{}/raw_file/{}".format(self.base_url, job_id, log_path)
        return self._get(url=url)

    def get_completion_date(self, job_info):
        completion_secs = job_info["completion_secs"]
        return datetime.fromtimestamp(completion_secs)

    def get_human_file(self, job_id, job_info=None, file_name=None, console_name=None):
        result = None

        try:
            if not job_info:
                response = self.get_job_by_id(job_id=job_id)
                job_info = json.loads(response)
            logs = job_info["basic_outputs"]
            for item in logs:
                log_info = None
                log_path = None
                if console_name:
                    name = item[0]
                    if console_name in name:
                        log_info = item[1]
                else:
                    log_info = item[1]
                if log_info:
                    if 'basename' in log_info:
                        if console_name:
                            log_path = log_info['basename']
                        else:
                            if file_name in log_info['basename']:
                                log_path = log_info['basename']
                        if log_path:
                            result = self.get_job_text_by_raw_path(job_id=job_id, log_path=log_path)
                            break
        except Exception as ex:
            fun_test.log("Actual response:" + response)
            fun_test.critical(str(ex))

        return result

    def add_palladium_job_info(self, job_dict):
        result = {}
        if "completion_secs" in job_dict:
            completion_date = self.get_completion_date(job_info=job_dict)
            lsf_id = job_dict["job_id"]
            jenkins_url = job_dict["jenkins_url"]
            build_properties_url = "{}artifact/bld_props.json".format(jenkins_url)
            build_properties = self._get(url=build_properties_url)
            suite_execution_id = fun_test.get_suite_execution_id()
            if build_properties is None:
                build_properties = ""
            add_jenkins_job_id_map(jenkins_job_id=job_dict["jenkins_build_number"],
                                   fun_sdk_branch=job_dict["branch_funsdk"],
                                   git_commit=job_dict["git_commit"],
                                   software_date=job_dict["software_date"],
                                   hardware_version=job_dict["hardware_version"],
                                   build_properties=build_properties, lsf_job_id=lsf_id, build_date=completion_date,
                                   suite_execution_id=suite_execution_id, add_associated_suites=False)
        else:
            print("XXX ERROR: Completion secs not found in job: {}".format(job_dict["job_id"]))
        return result

    def prepare_run_time_properties(self, job_dict):
        result = {}
        result["lsf_info"] = {}
        result["jenkins_info"] = {}
        result["suite_info"] = {}
        if "completion_secs" in job_dict:
            lsf_id = job_dict["job_id"]
            jenkins_url = job_dict["jenkins_url"]
            build_properties_url = "{}artifact/bld_props.json".format(jenkins_url)
            build_properties = self._get(url=build_properties_url)
            suite_execution_id = fun_test.get_suite_execution_id()
            if build_properties is None:
                build_properties = {}
            else:
                build_properties = json.loads(build_properties)
            result["lsf_info"] = {"lsf_job_id": lsf_id}
            result["suite_info"] = {"suite_execution_id": suite_execution_id,
                                    "associated_suites": []}
            result["jenkins_info"] = {"build_properties": build_properties}
        return result


if __name__ == "__main__":
    lsf = LsfStatusServer()
    # print lsf.health()
    lsf.get_last_job(tag="qa_triage_110_ab8ea7c")
