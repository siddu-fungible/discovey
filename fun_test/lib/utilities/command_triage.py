from lib.utilities.git_utilities import GitManager
from lib.utilities.jenkins_manager import JenkinsManager
import time
import json

log_file = "triage_log.txt"

BUILD_PARAMS = {
    "RUN_TARGET": "F1",
    "HW_MODEL": "F1DevBoard",
    "HW_VERSION": "Ignored",
    "RUN_MODE": "Batch",
    "PRIORITY": "high_priority",
    "BOOTARGS": "",
    "MAX_DURATION": 5,
    "SECURE_BOOT": "fungible",
    "NOTE": "",
    "FAST_EXIT": "true",
    "TAGS": "",
    "EXTRA_EMAIL": "ashwin.s@fungible.com,john.abraham@fungible.com",
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
    "FUNOS_MAKEFLAGS": "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list",
    "BRANCH_FunJenkins": "",
    "BRANCH_FunDevelopment": "",
    "BRANCH_FunTools": "",
    "RUN_PIPELINE": ""
}



def do_score_triage(commits, bootargs, base_tag):
    num_commits = len(commits)
    step = num_commits/4
    if step == 0:
        step = 1

    for i in range(0, len(commits), step):

        sha = commits[i]["sha"]
        tag = "{}_{}".format(base_tag, i)
        jenkins_manager = JenkinsManager(job_name="emulation/fun_on_demand")
        params = BUILD_PARAMS
        params["BOOTARGS"] = bootargs
        params["BRANCH_FunOS"] = sha
        #params["SECURE_BOOT"] = "Yes"
        params["DISABLE_ASSERTIONS"] = "true"
        params["TAGS"] = "{}, {}".format(tag, "qa_triage")
        queue_item = jenkins_manager.build(params=params)

        build_number = None
        while not build_number:
            time.sleep(3)
            build_number = jenkins_manager.get_build_number(queue_item=queue_item)
            if build_number:
                break
        print "Found build number: {}".format(build_number)

        '''
        job_info = jenkins_manager.get_job_info(build_number=build_number)
        while job_info["building"]:
            j = jenkins_manager.get_job_info(build_number=build_number)
            time.sleep(3)
        
        print "Result: {}".format(job_info["result"])
        '''
        f = open(log_file, "a+")
        d = {"index": i, "tag": tag, "sha": sha, "jenkins_build": build_number}
        f.write(json.dumps(d))
        f.write("\n")
        f.close()
        time.sleep(30)
        pass

if __name__ == "__main__":
    gm = GitManager()

    from_sha = "23c650af59406ca6df7783ca7b3f93605c0172ad"
    to_sha = "8713dd60ca4314a432b860468819e55f2768a114"

    commits = gm.get_commits_between(from_sha=from_sha, to_sha=to_sha)
    print("Num commits: {}".format(len(commits)))
    for commit in commits:
        print commit["sha"], commit["commit"]["committer"]["date"]
    bootargs = "--serial app=bcopy_speed_test,bcopy_flood_speed_test"
    bootargs = "app=soak_dma_memcpy"
    iteration = 1
    base_tag = "qa_triage_soak_dma_below_4k_{}".format(iteration)
    do_score_triage(commits, bootargs=bootargs, base_tag=base_tag)