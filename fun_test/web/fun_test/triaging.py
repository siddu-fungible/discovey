from datetime import datetime
import json
import random
import re
import jenkins, sys
import requests
from django.core.exceptions import ObjectDoesNotExist
import web.fun_test.django_interactive
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.metrics_models import MetricChart, MetricChartStatus, TriageFlow, Triage, LastTriageId, \
    LastTriageFlowId
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import SchedulingStates
from lib.host.lsf_status_server import LsfStatusServer
from lib.system.fun_test import *

BASE_TAG = "qa_triage"
JENKINS_URL = "http://jenkins-sw-master:8080/"
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

#"FUNOS_MAKEFLAGS": "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list",

jenkins_server = jenkins.Jenkins(JENKINS_URL, username='jenkins.service', password='117071d3cb2cae6c964099664b271e4011')

QA_TRIAGE = "qa_triage_"


@csrf_exempt
@api_safe_json_response
def fetch_triage_flow(request):
    request_json = json.loads(request.body)
    triage_id = request_json["triage_id"]
    result = {}
    result["flows"] = []
    result["triage"] = []
    try:
        triage = Triage.objects.filter(triage_id=triage_id)
        if len(triage):
            triage_details = triage[0]
            commit_detail = {}
            commit_detail["metric_id"] = triage_details.metric_id if triage_details.metric_id else None
            commit_detail["triage_id"] = triage_details.triage_id if triage_details.triage_id else None
            commit_detail["metric_type"] = triage_details.metric_type if triage_details.metric_type else None
            commit_detail[
                "last_good_score"] = triage_details.last_good_score if triage_details.last_good_score else None
            commit_detail[
                "degraded_score"] = triage_details.last_good_score if triage_details.last_good_score else None
            commit_detail["status"] = triage_details.status if triage_details.status else None
            commit_detail["max_tries"] = triage_details.max_tries if triage_details.max_tries else None
            commit_detail["faulty_commit"] = triage_details.faulty_commit if triage_details.faulty_commit else None
            commit_detail["date_time"] = triage_details.date_time if triage_details.date_time else None
            result["triage"].append(commit_detail)
        entries = TriageFlow.objects.filter(triage_id=triage_id).order_by("-date_time")
        if len(entries):
            for commit in entries:
                commit_detail = {}
                commit_detail["flow_id"] = commit.triage_flow_id if commit.triage_flow_id else None
                commit_detail["git_commit"] = commit.git_commit if commit.git_commit else None
                commit_detail["committer"] = commit.committer if commit.committer else None
                commit_detail["status"] = commit.status if commit.status else None
                commit_detail["jenkins"] = commit.jenkins_job_id if commit.jenkins_job_id else None
                commit_detail["lsf"] = commit.lsf_job_id if commit.lsf_job_id else None
                commit_detail["suite"] = commit.suite_execution_id if commit.suite_execution_id else None
                commit_detail["score"] = commit.score if commit.score else None
                result["flows"].append(commit_detail)
    except ObjectDoesNotExist:
        print "Error"
    return result


@csrf_exempt
@api_safe_json_response
def insert_triage_db(request):
    request_json = json.loads(request.body)
    commits = request_json["commits"]
    triage_info = request_json["triage_info"]

    degraded_suite_id = triage_info["degraded_suite_execution_id"]
    degraded_jenkins_job_id = triage_info["degraded_jenkins_job_id"]
    degraded_lsf_job_id = triage_info["degraded_lsf_job_id"]
    degraded_git_commit = commits[0]["hexsha"] if commits[-1]["hexsha"] else None
    degraded_jenkins = JenkinsJobIdMap.objects.filter(jenkins_job_id=degraded_jenkins_job_id)
    degraded_build_properties = degraded_jenkins[0].build_properties if degraded_jenkins and degraded_jenkins[
        0].build_properties else ""

    passed_suite_id = triage_info["passed_suite_execution_id"]
    passed_jenkins_job_id = triage_info["passed_jenkins_job_id"]
    passed_lsf_job_id = triage_info["passed_lsf_job_id"]
    passed_git_commit = commits[-1]["hexsha"] if commits[0]["hexsha"] else None
    passed_jenkins = JenkinsJobIdMap.objects.filter(jenkins_job_id=passed_jenkins_job_id)
    passed_build_properties = passed_jenkins[0].build_properties if passed_jenkins and passed_jenkins[
        0].build_properties else ""

    passed_score = triage_info["passed_score"]
    degraded_score = triage_info["degraded_score"]
    metric_type = triage_info["metric_type"]
    boot_args = triage_info["boot_args"]
    funOS_make_flags = triage_info["funOS_make_flags"]
    email = triage_info["email"]
    triage = Triage.objects.filter(degraded_git_commit=degraded_git_commit,
                                   stable_git_commit=passed_git_commit)
    if triage:
        return triage.triage_id
    else:
        triage_id = LastTriageId.get_next_id()
        triage = Triage(triage_id=triage_id, degraded_suite_execution_id=degraded_suite_id,
                        degraded_jenkins_job_id=degraded_jenkins_job_id, degraded_lsf_job_id=degraded_lsf_job_id,
                        degraded_git_commit=degraded_git_commit, degraded_build_properties=degraded_build_properties,
                        stable_suite_execution_id=passed_suite_id, stable_jenkins_job_id=passed_jenkins_job_id,
                        stable_lsf_job_id=passed_lsf_job_id, stable_git_commit=passed_git_commit,
                        stable_build_properties=passed_build_properties, last_good_score=passed_score, max_tries=5,
                        metric_type=metric_type, boot_args=boot_args, funOS_make_flags=funOS_make_flags, email=email)
        triage.save()
        for commit in commits[1:-1]:
            triage_flow = TriageFlow(triage_id=triage_id,
                                     triage_flow_id=LastTriageFlowId.get_next_id(),
                                     git_commit=commit["hexsha"], committer=commit["author"],
                                     build_properties=passed_build_properties, metric_type=metric_type,
                                     date_time=commit["date"], boot_args=boot_args, funOS_make_flags=funOS_make_flags, email=email)
            triage_flow.save()
        return triage_id


@csrf_exempt
@api_safe_json_response
def update_triage(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    faulty_commit = request_json["faulty_commit"]
    result = {}
    triage = Triage.objects.filter(metric_id=metric_id)
    if len(triage):
        triage_details = triage[0]
        triage_details.status = SchedulingStates.COMPLETED
        triage_details.faulty_commit = faulty_commit
        triage_details.save()
        result["faulty_commit"] = triage_details.faulty_commit
        result["status"] = triage_details.status
    return result


@csrf_exempt
@api_safe_json_response
def kill_triage(request):
    request_json = json.loads(request.body)
    triage_id = request_json["triage_id"]
    result = False
    triage = Triage.objects.filter(triage_id=triage_id)
    if len(triage):
        triage_details = triage[0]
        triage_details.status = SchedulingStates.ABORTED
        triage_details.save()
        triage_flow_entries = TriageFlow.objects.filter(triage_id=triage_details.triage_id)
        for entry in triage_flow_entries:
            if entry.status != "Completed" or entry.status != "Failed":
                entry.status = SchedulingStates.SUSPENDED
                entry.save()
        result = True
    return result

@csrf_exempt
@api_safe_json_response
def rerun_triage_flow(request):
    request_json = json.loads(request.body)
    triage_flow_id = request_json["triage_flow_id"]
    result = False
    triage_flow = TriageFlow.objects.filter(triage_flow_id=triage_flow_id)
    if len(triage_flow):
        triage_flow.status = SchedulingStates.WAITING
        triage_flow.save()
        triage_id = triage_flow.triage_id
        triage = Triage.objects.filter(triage_id=triage_id)
        if len(triage):
            triage.status = SchedulingStates.ACTIVE
            triage.save()

        result = True
    return result

@csrf_exempt
@api_safe_json_response
def check_triage(request):
    request_json = json.loads(request.body)
    triage_id = request_json["triage_id"]
    result = {}
    triage = Triage.objects.filter(triage_id=triage_id)
    if len(triage):
        result["metric_type"] = triage[0].metric_type
        result["from_commit"] = triage[0].degraded_git_commit
        result["to_commit"] = triage[0].stable_git_commit
        result["boot_args"] = triage[0].boot_args
        result["funOS_make_flags"] = triage[0].funOS_make_flags
        result["email"] = triage[0].email
    return result


def update_triaging():
    while True:
        result = None
        charts = Triage.objects.all()
        for chart in charts:
            if chart.triage_id:
                if chart.status == SchedulingStates.ACTIVE:
                    result = update_triage_flow(chart.triage_id, chart)
                    if result.content:
                        response = json.loads(result.content)
                        if response["data"]:
                            chart.status = SchedulingStates.COMPLETED
                            chart.save()
        time.sleep(60)


@csrf_exempt
@api_safe_json_response
def update_triage_flow(triage_id, triage_details):
    result = None
    entries = TriageFlow.objects.filter(triage_id=triage_id).order_by("-date_time")
    metric_type = triage_details.metric_type
    boot_args = triage_details.boot_args
    funOS_make_flags = triage_details.funOS_make_flags
    email = triage_details.email
    if metric_type == "PASS/FAIL":
        if len(entries):
            result = start_flow(entries, 0, len(entries) - 1, boot_args, funOS_make_flags, email)
        if result:
            print "all flows completed"
            return result
    print "one try finished"


def start_flow(entries, l, r, boot_args, funOS_make_flags, email):
    if r >= l:
        mid = l + (r - l) / 2
        entry = entries[mid]
        if entry.status == SchedulingStates.WAITING:
            tags = BASE_TAG
            BUILD_PARAMS["TAGS"] = tags
            BUILD_PARAMS["BOOTARGS"] = boot_args
            BUILD_PARAMS["BRANCH_FunOS"] = entry.git_commit
            BUILD_PARAMS["FUNOS_MAKEFLAGS"] = funOS_make_flags
            BUILD_PARAMS["EXTRA_EMAIL"] = email
            try:
                entry.status = SchedulingStates.SELECTED_FOR_TRIAL
                entry.save()
                next_build_number = jenkins_server.get_job_info('emulation/fun_on_demand')['nextBuildNumber']
                output = jenkins_server.build_job('emulation/fun_on_demand', BUILD_PARAMS)
                time.sleep(10)
                build_info = jenkins_server.get_build_info('emulation/fun_on_demand', next_build_number)
                entry.status = SchedulingStates.BUILDING_ON_JENKINS
                entry.jenkins_job_id = build_info["number"]
                entry.boot_args = boot_args
                entry.funOS_make_flags = funOS_make_flags
                entry.email = email
                entry.save()
                print "Added a flow"
            except:
                entry.status = SchedulingStates.SUBMITTED_TO_JENKINS
                entry.save()
        elif entry.status == SchedulingStates.COMPLETED:
            suspend_flows(entry, entries, mid, l, r)
            print "suspended flows"
            return start_flow(entries, l, mid - 1, boot_args, funOS_make_flags, email)
        elif entry.status == SchedulingStates.FAILED:
            suspend_flows(entry, entries, mid, l, r)
            print "suspended flows"
            return start_flow(entries, mid + 1, r, boot_args, funOS_make_flags, email)
        elif entry.status == SchedulingStates.BUILDING_ON_JENKINS:
            try:
                build_number = entry.jenkins_job_id
                info = jenkins_server.get_build_info('emulation/fun_on_demand', build_number)
                if not info["building"]:
                    if info["result"] == "SUCCESS":
                        entry.status = SchedulingStates.JENKINS_BUILD_COMPLETE
                        entry.save()
            except:
                pass
        elif entry.status == SchedulingStates.JENKINS_BUILD_COMPLETE:
            try:
                info = jenkins_server.get_build_info('emulation/fun_on_demand', entry.jenkins_job_id)
                description = info["description"]
                m = re.search(
                    r'"http://palladium-jobs.fungible.local:8080/job/(?P<lsf_job_id>\S+)"',
                    description)
                if m:
                    lsf_job_id = int(m.group('lsf_job_id'))
                    entry.lsf_job_id = lsf_job_id
                    entry.status = SchedulingStates.RUNNING_ON_LSF
                    entry.save()
            except:
                pass
        elif entry.status == SchedulingStates.RUNNING_ON_LSF:
            try:
                result = validate_job(lsf_job_id=entry.lsf_job_id, validation_required=True)
                if result["passed"]:
                    entry.status = SchedulingStates.COMPLETED
                else:
                    entry.status = SchedulingStates.FAILED
                entry.save()
            except:
                pass
    else:
        return "Completed"


def suspend_flows(entry, entries, mid, l, r):
    if entry.status == SchedulingStates.COMPLETED:
        index = mid + 1
        while index <= r:
            updating_entry = entries[index]
            if updating_entry.status == SchedulingStates.WAITING:
                updating_entry.status = SchedulingStates.SUSPENDED
                updating_entry.save()
            index = index + 1
    if entry.status == SchedulingStates.FAILED:
        while l < mid:
            updating_entry = entries[l]
            if updating_entry.status == SchedulingStates.WAITING:
                updating_entry.status = SchedulingStates.SUSPENDED
                updating_entry.save()
            l = l + 1


def validate_job(lsf_job_id, validation_required=True):
    lsf_status_server = LsfStatusServer()
    result = {}
    if lsf_job_id:
        try:
            job_info = lsf_status_server.get_job_by_id(lsf_job_id)
            fun_test.test_assert(job_info, "Ensure Job Info exists")
            response_dict = json.loads(job_info)
            status = response_dict["job_dict"]["return_code"]
            if not status:
                print "Passed"
                result["passed"] = True
            else:
                print "Failed"
                result["passed"] = False
        except:
            pass
    return result
    # job_info = lsf_status_server.get_last_job(tag=tag)
    # fun_test.test_assert(job_info, "Ensure Job Info exists")
    # jenkins_job_id = job_info["jenkins_build_number"]
    # job_id = job_info["job_id"]
    # result["lsf_job_id"] = job_id
    # result["jenkins_job_id"] = jenkins_job_id
    # result["passed"] = False
    # git_commit = job_info["git_commit"]
    # git_commit = git_commit.replace("https://github.com/fungible-inc/FunOS/commit/", "")
    # if validation_required:
    #     if job_info["return_code"]:
    #         return result
    #     else:
    #         result["passed"] = True
    #     fun_test.test_assert(not job_info["return_code"], "Valid return code")
    #     fun_test.test_assert("output_text" in job_info, "output_text found in job info: {}".format(job_id))
    # lines = job_info["output_text"].split("\n")
    # dt = job_info["date_time"]
    # return result


if __name__ == "__main__":
    # validate_job(tag="qa_triage", validation_required=True)
    update_triaging()

if __name__ == "__main_test__":
    metric_id = 157
    # update_triage_flow(metric_id=metric_id)
    # job = Jenkins.get_job('emulation/fun_on_demand')
    # build = job.get_last_build()
    # parameters = build.get_actions()['parameters']
    # BUILD_PARAMS["BOOTARGS"] = "app=perftest_deflate,perftest_lzma --serial"
    # BUILD_PARAMS["BRANCH_FunOS"] = "0380baac5846806ea6510dd853c7fc4cf8612afa"
    # BUILD_PARAMS["DISABLE_ASSERTIONS"] = "true"
    # BUILD_PARAMS["TAGS"] = "qa_branch_prediction"
    # BUILD_PARAMS["NOTE"] = "Zip apps - branch prediction"
    # jenkins_server.build_job('emulation/fun_on_demand', BUILD_PARAMS)
    print "started"
    # server = jenkins.Jenkins(url=JENKINS_URL, username='jenkins.service', password='117071d3cb2cae6c964099664b271e4011')
    # user = server.get_whoami()
    # print('Hello %s from Jenkins %s' % (user['fullName'], version))
    # server.create_job("empty", config_xml=jenkins.EMPTY_CONFIG_XML)
    # server.build_job('emulation/fun_on_demand', params)
    # job = jenkins_server.get_job("emulation/fun_on_demand")
    # job = jenkins_server.get_job
    # info = jenkins_server.get_build_info('emulation/fun_on_demand', 3640)
    # queue_number = jenkins_server.build_job('emulation/fun_on_demand', BUILD_PARAMS)
    # time.sleep(5)
    # next_build_number = jenkins_server.get_job_info('emulation/fun_on_demand')['nextBuildNumber']
    # output = jenkins_server.build_job('emulation/fun_on_demand', BUILD_PARAMS)
    # time.sleep(10)
    build_info = jenkins_server.get_build_info('emulation/fun_on_demand', 3657)
    lsf_job_id = 632460
    validate_job(lsf_job_id=lsf_job_id)
    print "completed"
    # my_job = server.get_job_config('emulation')
    # print(my_job)  # prints XML configuration
    # # print jobs
    # curl_params = [
    # {"name": "RUN_TARGET", "value": "F1"},
    # {"name": "HW_MODEL", "value": "F1DevBoard"},
    # {"name": "HW_VERSION", "value": "ignored"},
    # {"name": "RUN_MODE", "value": "Batch"},
    # {"name": "PRIORITY", "value": "normal_priority"},
    # {"name": "BOOTARGS", "value": "app=soak_malloc_classic"},
    # {"name": "MAX_DURATION", "value": 20},
    # {"name": "FAST_EXIT", "value": True}
    # ]
