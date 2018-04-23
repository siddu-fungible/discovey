import requests
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
        print self._get(url=url)


if __name__ == "__main__":
    lsf = LsfStatusServer()
    # print lsf.health()
    lsf.get_jobs_by_tag(tag="alloc_speed_test")