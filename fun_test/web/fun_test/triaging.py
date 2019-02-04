from datetime import datetime
import json
import random
from django.core.exceptions import ObjectDoesNotExist
import web.fun_test.django_interactive
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.metrics_models import MetricChart, MetricChartStatus, TriageFlow, Triage, LastTriageId
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import SchedulingStates


@csrf_exempt
@api_safe_json_response
def update_triage(triage_id):
    entries = TriageFlow.objects.filter(triage_id=triage_id)
    pick = False
    for entry in entries:
        if pick:
            entry.score = random.randint(70,100)
            entry.status = SchedulingStates.SUCCCESS
            entry.suite_execution_id = 1234
            entry.jenkins_job_id = 4444
            entry.lsf_job_id = 12345
            entry.save()
        pick = not pick


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
            commit_detail["last_good_score"] = triage_details.last_good_score if triage_details.last_good_score else None
            commit_detail["status"] = triage_details.status if triage_details.status else None
            result["triage"].append(commit_detail)
        entries = TriageFlow.objects.filter(metric_id=metric_id)
        if len(entries):
            for commit in entries:
                commit_detail = {}
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
    triage = Triage.objects.filter(metric_id=metric_id)
    if triage:
        return 0
    else:
        triage_id = LastTriageId.get_next_id()
        triage = Triage(metric_id=metric_id, triage_id=triage_id, degraded_suite_execution_id=degraded_suite_id,
                    degraded_jenkins_job_id=degraded_jenkins_job_id, degraded_lsf_job_id=degraded_lsf_job_id,
                    degraded_git_commit=degraded_git_commit, degraded_build_properties=degraded_build_properties,
                    stable_suite_execution_id=passed_suite_id, stable_jenkins_job_id=passed_jenkins_job_id,
                    stable_lsf_job_id=passed_lsf_job_id, stable_git_commit=passed_git_commit,
                    stable_build_properties=passed_build_properties, last_good_score=passed_score)
        triage.save()
        for commit in commits[1:-1]:
            triage_flow = TriageFlow(metric_id=metric_id, triage_id=triage_id, git_commit=commit["hexsha"],
                                     committer=commit["author"], build_properties=passed_build_properties)
            triage_flow.save()
    return 1

if __name__ == "__main__":
    triage_id = 113
    update_triage(triage_id=triage_id)
    print "completed"
