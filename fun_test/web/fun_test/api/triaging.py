from web.web_global import api_safe_json_response
from fun_global import get_current_time, RESULTS
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.metrics_models import Triage3, Triage3Trial, LastTriageId
from web.fun_test.triaging_global import TriageTrialStates, TriagingStates, TriagingTypes
from django.db.models import Q
import json
from lib.utilities.git_utilities import GitManager


@csrf_exempt
@api_safe_json_response
def trial_set(request, triage_id):
    request_json = json.loads(request.body)
    from_fun_os_sha = request_json.get("from_fun_os_sha")
    to_fun_os_sha = request_json.get("to_fun_os_sha")
    t = Triage3.objects.get(triage_id=triage_id)
    t.current_trial_set_id += 1
    t.current_trial_from_sha = from_fun_os_sha
    t.current_trial_to_sha = to_fun_os_sha
    t.save()


def long_to_short_sha(long_sha):
    return long_sha[:7]

def get_trial_tag(base_tag, triage_id, fun_os_sha):  #TODO
    return "{}_{}_{}".format(base_tag, triage_id, long_to_short_sha(fun_os_sha))

@csrf_exempt
@api_safe_json_response
def trials(request, triage_id, fun_os_sha):
    triage_id = int(triage_id)
    result = None
    if request.method == "POST":
        if fun_os_sha:
            q = Q(triage_id=triage_id, fun_os_sha=fun_os_sha)
            trials = Triage3Trial.objects.filter(q).order_by('submission_date_time')
            if trials.count():
                first_trial = trials[0]
                # TrialReRuns(fun_os_sha=first_trial.fun_os_sha,
                #                      triage_id=first_trial.triage_id,
                #                      trial_set_id=first_trial.trial_set_id,
                #                      status=first_trial.status,
                #                      jenkins_build_number=first_trial.jenkins_build_number,
                #                      lsf_job_id=first_trial.lsf_job_id,
                #                      tag=first_trial.tag,
                #                      regex_match=first_trial.regex_match,
                #                      submission_date_time=first_trial.submission_date_time,
                #                      tags=first_trial.tags,
                #                      result=first_trial.result).save()
                request_json = json.loads(request.body)
                status = request_json.get("status", None)
                if status is not None:
                    first_trial.status = int(status)
                tag = request_json.get("tag", None)
                if tag is not None:
                    first_trial.tag = tag

                tags = request_json.get("tags", None)
                if tags is not None:
                    first_trial.tags = tags
                if first_trial.status == TriageTrialStates.INIT:
                    triage = Triage3.objects.get(triage_id=triage_id)
                    triage.status = TriagingStates.IN_PROGRESS
                    triage.save()
                first_trial.result = RESULTS["UNKNOWN"]
                # first_trial.re_runs = True
                first_trial.save()
            else:
                request_json = json.loads(request.body)
                t = Triage3.objects.get(triage_id=triage_id)
                fun_os_sha = request_json["fun_os_sha"]
                trial = Triage3Trial(fun_os_sha=fun_os_sha,
                                     triage_id=triage_id,
                                     trial_set_id=t.current_trial_set_id,
                                     status=TriagingStates.INIT,
                                     submission_date_time=get_current_time())
                trial_tag = get_trial_tag(base_tag="qa_triage", triage_id=triage_id, fun_os_sha=fun_os_sha)
                trial.tag = trial_tag
                trial.save()
    elif request.method == "GET":
        q = Q(triage_id=triage_id)
        if fun_os_sha:
            q = q & Q(fun_os_sha=fun_os_sha)
        trials = Triage3Trial.objects.filter(q).order_by('-submission_date_time')
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
                          "regex_match": trial.regex_match,
                          "tags": trial.tags,
                          "result": trial.result}
            # if trial.re_runs:
            #     one_record["history"] =
            result.append(one_record)
    return result


@csrf_exempt
@api_safe_json_response
def triagings(request, triage_id):
    result = None
    if request.method == "POST":
        if not triage_id:
            request_json = json.loads(request.body)
            metric_id = request_json.get("metric_id", None)

            triage_type = int(request_json.get("triage_type", TriagingTypes.REGEX_MATCH))
            from_fun_os_sha = request_json["from_fun_os_sha"]
            to_fun_os_sha = request_json["to_fun_os_sha"]
            submitter_email = request_json["submitter_email"]
            build_parameters = request_json.get("build_parameters", None)
            blob = request_json.get("blob", None)
            if triage_type == TriagingTypes.REGEX_MATCH:
                regex_match_string = request_json["regex_match_string"]

            triage_id = LastTriageId.get_next_id()

            regex_match_string = request_json.get("regex_match_string", None)

            t = Triage3(triage_id=triage_id,
                        triage_type=triage_type,
                        from_fun_os_sha=from_fun_os_sha,
                        to_fun_os_sha=to_fun_os_sha,
                        submitter_email=submitter_email)
            if build_parameters is not None:
                t.build_parameters = build_parameters
            if blob is not None:
                t.blob = blob
            if metric_id is not None:
                t.metric_id = metric_id
            if regex_match_string is not None:
                t.regex_match_string = regex_match_string
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


@csrf_exempt
@api_safe_json_response
def triaging_types(request):
    return TriagingTypes().all_strings_to_code()
