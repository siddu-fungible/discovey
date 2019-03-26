import jenkins
import time
import re
import requests
from requests.auth import HTTPBasicAuth


DEFAULT_BUILD_PARAMS = {
    "RUN_TARGET": "F1",
    "HW_MODEL": "F1DevBoard",
    "HW_VERSION": "Ignored",
    "RUN_MODE": "Build only",
    "PRIORITY": "high_priority",
    "BOOTARGS": "app=jpeg_perf_test --disable-wu-watchdog --test-exit-fast",
    "MAX_DURATION": 3,
    "SECURE_BOOT": "fungible",
    "NOTE": "",
    "FAST_EXIT": "true",
    "TAGS": "",
    "EXTRA_EMAIL": "john.abraham@fungible.com",
    "BRANCH_FunOS": "",
    "DISABLE_ASSERTIONS": "false",
    "PCI_MODE": "",
    "REMOTE_SCRIPT": "",
    "NETWORK_MODE": "",
    "NETWORK_SCRIPT": "",
    "UART_MODE": "",
    "UART_SCRIPT": "",
    "BRANCH_FunSDK": "",
    "BRANCH_FunHW": "",
    "BRANCH_pdclibc": "",
    "BRANCH_SBPFirmware": "",
    "BRANCH_u_boot": "",
    "BRANCH_mbedtls": "",
    "BRANCH_aapl": "",
    "ENABLE_WULOG": "false",
    "CSR_FILE": "",
    "WAVEFORM_CMD": "",
    "HBM_DUMP": "",
    "FUNOS_MAKEFLAGS": "",
    "BRANCH_FunJenkins": "",
    "BRANCH_FunDevelopment": "",
    "BRANCH_FunTools": "",
    "RUN_PIPELINE": ""
}

class JenkinsManager():
    JENKINS_BASE_URL = "http://jenkins-sw-master:8080/"
    SERVICE_PASSWORD = '117071d3cb2cae6c964099664b271e4011'
    SERVICE_USERNAME = 'jenkins.service'
    def __init__(self, job_name):
        self.jenkins_server = jenkins.Jenkins(self.JENKINS_BASE_URL, username=self.SERVICE_USERNAME,
                                     password=self.SERVICE_PASSWORD)
        self.job_name = job_name

    def _apply_params(self, user_params):
        params = dict(DEFAULT_BUILD_PARAMS)
        for key, value in user_params.iteritems():
            if key in params:
                params[key] = value
            else:
                raise Exception("Key: {} is not in the BUILD params".format(key))
        return params

    def build(self, params):
        # self.jenkins_server.get_job_info('emulation/fun_on_demand', build_number)
        queue_item = self.jenkins_server.build_job(self.job_name, self._apply_params(user_params=params))
        return queue_item

    def get_build_number(self, queue_item):
        build_number = None
        status = self.jenkins_server.get_queue_item(number=queue_item)
        if "executable" in status:
            if "number" in status["executable"]:
                build_number = status["executable"]["number"]
        return build_number

    def get_job_info(self, build_number):
        info = self.jenkins_server.get_build_info(self.job_name, build_number)
        return info

    def get_node_number(self, build_number):
        result = None
        url = "{}/job/emulation/job/fun_on_demand/{}/ws/".format(self.JENKINS_BASE_URL, build_number)
        r = requests.get(url, auth=HTTPBasicAuth(self.SERVICE_USERNAME, self.SERVICE_PASSWORD))
        if r.status_code == 200:
            m = re.findall(r'/job/emulation/job/fun_on_demand/{}/execution/node/(\d+)/ws/'.format(build_number), r.content)
            if len(m) > 0:
                result = m[-1]
        return result

    def get_emulation_image_path(self, build_number, node_number):
        s = "/job/emulation/job/fun_on_demand/{}/execution/node/{}/ws/emulation_image/funos-f1.stripped".format(build_number, node_number)
        return s

    def download_file(self, source_path, target_path):
        url = "{}{}".format(self.JENKINS_BASE_URL, source_path)
        r = requests.get(url, auth=HTTPBasicAuth(self.SERVICE_USERNAME, self.SERVICE_PASSWORD))
        open(target_path, 'wb').write(r.content)

if __name__ == "__main__":
    jenkins_manager = JenkinsManager()
    boot_args = "app=jpeg_perf_test --disable-wu-watchdog --test-exit-fast"
    params = {"BOOTARGS": boot_args, "FUNOS_MAKEFLAGS": "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list"}

    queue_item = jenkins_manager.build(params=params)
    build_number = None
    while not build_number:
        time.sleep(3)
        build_number = jenkins_manager.get_build_number(queue_item=queue_item)
        if build_number:
            break
    print "Found build number: {}".format(build_number)

    job_info = jenkins_manager.get_job_info(build_number=build_number)
    while job_info["building"]:
        j = jenkins_manager.get_job_info(build_number=build_number)
        time.sleep(3)

    print "Result: {}".format(job_info["result"])
    node_number = jenkins_manager.get_node_number(build_number=build_number)
    jenkins_manager.download_file(source_path=jenkins_manager.get_emulation_image_path(build_number=build_number,
                                                                               node_number=node_number), target_path='/tmp/f1-stripped')