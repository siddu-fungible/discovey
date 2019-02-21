from datetime import datetime
import json
import random
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

pick_values = {0: 78.5,
               1: 75.4,
               2: 74.3,
               3: 72.1,
               4: 70}

@csrf_exempt
@api_safe_json_response
def update_triage_flow(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    entries = TriageFlow.objects.filter(metric_id=metric_id).order_by("-date_time")
    triage_details = None
    triage = Triage.objects.filter(metric_id=metric_id)
    if len(triage):
        triage_details = triage[0]
        last_good_score = triage_details.last_good_score
        if len(entries):
            update_mid(entries, 0, len(entries) - 1, last_good_score, 0)
            print "updated"


def update_mid(entries, l, r, last_good_score, id):
    if r >= l:
        mid = l + (r - l) / 2
        entry = entries[mid]
        if entry.score == -1:
            # entry.score = round(random.uniform(70, 80), 2)
            entry.score = pick_values[id]
            entry.status = SchedulingStates.COMPLETED
            entry.suite_execution_id = 1234
            entry.jenkins_job_id = 4444
            entry.lsf_job_id = 12345
            entry.date_time = entry.date_time
            entry.save()

            suspend_flows(entry, entries, last_good_score, mid, l, r)
        else:
            if entry.score >= last_good_score:
                update_mid(entries, l, mid - 1, last_good_score, id + 1)
            if entry.score < last_good_score:
                update_mid(entries, mid + 1, r, last_good_score, id + 1)

def suspend_flows(entry, entries, last_good_score, mid, l, r):
    if entry.score >= last_good_score:
        index = mid + 1
        while index <= r:
            updating_entry = entries[index]
            if updating_entry.status == SchedulingStates.ACTIVE:
                updating_entry.status = SchedulingStates.SUSPENDED
                updating_entry.save()
            index = index + 1
    if entry.score < last_good_score:
        while l < mid:
            updating_entry = entries[l]
            if updating_entry.status == SchedulingStates.ACTIVE:
                updating_entry.status = SchedulingStates.SUSPENDED
                updating_entry.save()
            l = l + 1

@csrf_exempt
@api_safe_json_response
def fetch_triage_flow(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    result = {}
    result["flows"] = []
    result["triage"] = []
    try:
        triage = Triage.objects.filter(metric_id=metric_id)
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
        entries = TriageFlow.objects.filter(metric_id=metric_id).order_by("-date_time")
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
    metric_id = request_json["metric_id"]
    commits = request_json["commits"]
    triage_info = request_json["triage_info"]

    degraded_suite_id = triage_info["degraded_suite_execution_id"]
    degraded_jenkins_job_id = triage_info["degraded_jenkins_job_id"]
    degraded_lsf_job_id = triage_info["degraded_lsf_job_id"]
    degraded_git_commit = commits[-1]["hexsha"] if commits[-1]["hexsha"] else None
    degraded_jenkins = JenkinsJobIdMap.objects.filter(jenkins_job_id=degraded_jenkins_job_id)
    degraded_build_properties = degraded_jenkins[0].build_properties if degraded_jenkins[0].build_properties else ""

    passed_suite_id = triage_info["passed_suite_execution_id"]
    passed_jenkins_job_id = triage_info["passed_jenkins_job_id"]
    passed_lsf_job_id = triage_info["passed_lsf_job_id"]
    passed_git_commit = commits[0]["hexsha"] if commits[0]["hexsha"] else None
    passed_jenkins = JenkinsJobIdMap.objects.filter(jenkins_job_id=passed_jenkins_job_id)
    passed_build_properties = passed_jenkins[0].build_properties if passed_jenkins[0].build_properties else ""

    passed_score = triage_info["passed_score"]
    degraded_score = triage_info["degraded_score"]
    metric_type = triage_info["metric_type"]
    boot_args = triage_info["boot_args"]
    triage = Triage.objects.filter(metric_id=metric_id, degraded_git_commit=degraded_git_commit, stable_git_commit=passed_git_commit)
    if triage:
        return 0
    else:
        triage_id = LastTriageId.get_next_id()
        triage = Triage(metric_id=metric_id, triage_id=triage_id, degraded_suite_execution_id=degraded_suite_id,
                        degraded_jenkins_job_id=degraded_jenkins_job_id, degraded_lsf_job_id=degraded_lsf_job_id,
                        degraded_git_commit=degraded_git_commit, degraded_build_properties=degraded_build_properties,
                        stable_suite_execution_id=passed_suite_id, stable_jenkins_job_id=passed_jenkins_job_id,
                        stable_lsf_job_id=passed_lsf_job_id, stable_git_commit=passed_git_commit,
                        stable_build_properties=passed_build_properties, last_good_score=passed_score, max_tries=5, metric_type=metric_type, boot_args=boot_args)
        triage.save()
        for commit in commits[1:-1]:
            triage_flow = TriageFlow(metric_id=metric_id, triage_id=triage_id,
                                     triage_flow_id=LastTriageFlowId.get_next_id(),
                                     git_commit=commit["hexsha"], committer=commit["author"],
                                     build_properties=passed_build_properties)
            triage_flow.save()
    return 1

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
        triage_details.status = SchedulingStates.SUCCESS
        triage_details.faulty_commit = faulty_commit
        triage_details.save()
        result["faulty_commit"] = triage_details.faulty_commit
        result["status"] = triage_details.status
    return result

@csrf_exempt
@api_safe_json_response
def check_triage(request):
    request_json = json.loads(request.body)
    metric_id = request_json["metric_id"]
    triage = Triage.objects.filter(metric_id=metric_id)
    if len(triage):
        return True
    return False


if __name__ == "__main__":
    metric_id = 157
    # update_triage_flow(metric_id=metric_id)
    url = "http://jenkins-sw-master:8080/"
    print "completed"
    server = jenkins.Jenkins(url=url, username='jenkins.service', password='117071d3cb2cae6c964099664b271e4011')
    user = server.get_whoami()
    print server.jobs_count()
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(server.get_jobs())
    print server.get_jobs()
    version = server.get_version()
    user = server.get_whoami()
    print('Hello %s from Jenkins %s' % (user['fullName'], version))
    # server.create_job("empty", config_xml=jenkins.EMPTY_CONFIG_XML)
    my_job = server.get_job_config('emulation')
    print(my_job)  # prints XML configuration
    print "hello"
    # jobs = server.get_jobs(view_name='Emulation')
    # print jobs
