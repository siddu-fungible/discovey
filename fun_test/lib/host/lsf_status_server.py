from lib.system.fun_test import fun_test
from fun_global import get_localized_time
from web.fun_test.models_helper import add_jenkins_job_id_map
import requests
import json
import pytz
from datetime import datetime
from dateutil import parser

LSF_WEB_SERVER_BASE_URL = "http://10.1.20.73:8080"


class LsfStatusServer:
    def __init__(self):
        self.base_url = LSF_WEB_SERVER_BASE_URL

    def health(self):
        url = "{}".format(self.base_url)
        response = requests.get(url)
        return response.status_code == 200

    def _get(self, url):
        data = None
        response = requests.get(url)
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
            last_job = past_jobs[0]
            local_past_jobs_index = fun_test.get_local_setting("lsf_past_jobs_index")
            if local_past_jobs_index:
                last_job = past_jobs[int(local_past_jobs_index)]
            job_id = last_job["job_id"]
            fun_test.add_checkpoint("Validating Job: {}".format(job_id))
            fun_test.log("Job Info: {}".format(fun_test.dict_to_json_string(last_job)))
            if validate:
                fun_test.add_checkpoint("Fetching return code for: {}".format(job_id))
                return_code = int(last_job["return_code"])
                fun_test.test_assert(not return_code, "Valid return code")
                fun_test.test_assert("output_text" in last_job, "output_text found in job info: {}".format(job_id))
            result = last_job
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_past_jobs_by_tag(self, tag, add_info_to_db=True):
        past_jobs = []
        jobs_by_tag_response = self.get_jobs_by_tag(tag=tag)
        if jobs_by_tag_response:
            response_dict = json.loads(jobs_by_tag_response)
            fun_test.log(json.dumps(response_dict, indent=4))
            past_jobs = response_dict["past_jobs"]

        if add_info_to_db:
            for past_job in past_jobs:
                job_info = past_job
                if "completion_date" not in job_info:
                    fun_test.critical("Job: {} has no field named completion_date".format(job_info["job_id"]))
                    continue
                completion_date = "20" + job_info["completion_date"]
                dt = get_localized_time(datetime.strptime(completion_date, "%Y-%m-%d %H:%M"))
                # dt = dt.astimezone(pytz.timezone('Etc/Greenwich'))
                self.add_palladium_job_info(job_info=job_info)
                response = self.get_job_by_id(job_id=job_info["job_id"])
                response = self.get_job_by_id(job_id=job_info["job_id"]) # Workaround
                try:
                    response_dict = json.loads(response)
                    fun_test.log(json.dumps(response_dict, indent=4))
                    output_text = response_dict["output_text"]
                    past_job["date_time"] = dt
                    past_job["output_text"] = output_text
                except Exception as ex:
                    fun_test.log("Actual response:" + response)
                    fun_test.critical(str(ex))
        return past_jobs

    def get_job_by_id(self, job_id):
        url = "{}/job/{}?format=json".format(self.base_url, job_id)
        return self._get(url=url)

    def add_palladium_job_info(self, job_info):
        try:
            self.get_job_by_id(job_id=job_info["job_id"])
            self.get_job_by_id(job_id=job_info["job_id"])
        except:
            pass
        result = {}
        if "completion_date" in job_info:
            completion_date = "20" + job_info["completion_date"]
            add_jenkins_job_id_map(jenkins_job_id=job_info["jenkins_build_number"],
                                                 fun_sdk_branch=job_info["branch_funsdk"],
                                                 git_commit=job_info["git_commit"],
                                                 software_date=job_info["software_date"],
                                                 hardware_version=job_info["hardware_version"],
                                                 completion_date=completion_date)
            dt = get_localized_time(datetime.strptime(completion_date, "%Y-%m-%d %H:%M"))
            response = self.get_job_by_id(job_id=job_info["job_id"])
            response = self.get_job_by_id(job_id=job_info["job_id"])
            response_dict = {"output_text": "-1"}
            try:
                response_dict = json.loads(response)
                print(json.dumps(response_dict, indent=4))
            except Exception as ex:
                fun_test.log("Actual response:" + response)
                fun_test.critical(str(ex))
        
            output_text = response_dict["output_text"]
            result["date_time"] = dt
            result["output_text"] = output_text
        else:
            print("XXX ERROR: Completion date not found in job: {}".format(job_info["job_id"]))
        return result


if __name__ == "__main__":
    lsf = LsfStatusServer()
    # print lsf.health()
    lsf.get_past_jobs_by_tag(tag="alloc_speed_test")