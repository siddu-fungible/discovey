from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.metrics_models import Triage3, Triage3Trial, LastTriageId
from web.fun_test.triaging_global import TriageTrialStates, TriagingStates
from django.db.models import Q
import json
from lib.utilities.git_utilities import GitManager


@csrf_exempt
@api_safe_json_response
def trials(request, triage_id, fun_os_sha):
    triage_id = int(triage_id)
    result = None
    if request.method == "POST":
        pass
    elif request.method == "GET":
        q = Q(triage_id=triage_id)
        if fun_os_sha:
            q = q & Q(fun_os_sha=fun_os_sha)
        trials = Triage3Trial.objects.filter(q).order_by('-pk')
        for trial in trials:
            if result is None:
                result = []
            one_record = {"triage_id": trial.triage_id,
                          "fun_os_sha": trial.fun_os_sha,
                          "trial_set_id": trial.trial_set_id,
                          "status": trial.status,
                          "jenkins_build_number": trial.jenkins_build_number,
                          "lsf_job_id": trial.lsf_job_id,
                          "tag": trial.tag,
                          "regex_match": trial.regex_match}
            result.append(one_record)
    return result


@csrf_exempt
@api_safe_json_response
def triagings(request, triage_id):
    result = None
    if request.method == "POST":
        if not triage_id:
            request_json = json.loads(request.body)
            metric_id = int(request_json["metric_id"])
            triage_type = request_json.get("triage_type", "REGEX_SEARCH")
            from_fun_os_sha = request_json["from_fun_os_sha"]
            to_fun_os_sha = request_json["to_fun_os_sha"]
            submitter_email = request_json["submitter_email"]
            build_parameters = request_json["build_parameters"]

            triage_id = LastTriageId.get_next_id()

            t = Triage3(triage_id=triage_id, metric_id=metric_id,
                        triage_type=triage_type,
                        from_fun_os_sha=from_fun_os_sha,
                        to_fun_os_sha=to_fun_os_sha, submitter_email=submitter_email, build_parameters=build_parameters)
            t.save()
            result = t.triage_id
        else:
            request_json = json.loads(request.body)
            triage_id = int(triage_id)
            t = Triage3.objects.get(triage_id=triage_id)
            status = request_json.get("status", None)
            if status is not None:
                t.status = status
                if status == TriagingStates.INIT:
                    t.current_trial_set_id = 1
            t.save()

    elif request.method == "GET":
        q = Q()
        if triage_id:
            q = q & Q(triage_id=triage_id)
        triages = Triage3.objects.filter(q).order_by('-submission_date_time')

        for triage in triages:
            if result is None:
                result = []
            one_record = {"triage_id": triage.triage_id,
                          "metric_id": triage.metric_id,
                          "triage_type": triage.triage_type,
                          "from_fun_os_sha": triage.from_fun_os_sha,
                          "to_fun_os_sha": triage.to_fun_os_sha,
                          "submitter_email": triage.submitter_email,
                          "build_parameters": triage.build_parameters,
                          "status": triage.status,
                          "result": triage.result,
                          "submission_date_time": triage.submission_date_time}
            if not triage_id:
                result.append(one_record)
            else:
                result = one_record
    return result


@csrf_exempt
@api_safe_json_response
def triaging_states(request):
    return TriagingStates().all_codes_to_string()


@csrf_exempt
@api_safe_json_response
def triaging_trial_states(request):
    return TriageTrialStates().all_codes_to_string()


@csrf_exempt
@api_safe_json_response
def git_commits_fun_os(request, from_sha, to_sha):
    gm = GitManager()
    commits_between = gm.get_commits_between(from_sha=from_sha, to_sha=to_sha)
    commits_between = [x.to_dict() for x in commits_between]
    return commits_between
