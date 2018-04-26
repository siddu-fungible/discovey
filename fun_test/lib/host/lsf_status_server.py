from lib.system.fun_test import fun_test
import requests
import json
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

    def get_past_jobs_by_tag(self, tag):
        past_jobs = []
        jobs_by_tag_response = self.get_jobs_by_tag(tag=tag)
        if jobs_by_tag_response:
            response_dict = json.loads(jobs_by_tag_response)
            fun_test.log(json.dumps(response_dict, indent=4))
            past_jobs = response_dict["past_jobs"]
        return past_jobs

    def get_job_by_id(self, job_id):
        url = "{}/job/{}?format=json".format(self.base_url, job_id)
        return self._get(url=url)

if __name__ == "__main__":
    lsf = LsfStatusServer()
    # print lsf.health()
    lsf.get_past_jobs_by_tag(tag="alloc_speed_test")