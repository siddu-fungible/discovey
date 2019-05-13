from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.metrics_models import Triage3, Triage3Trial
from web.fun_test.triaging_global import TriageTrialStates, TriagingStates
from django.db.models import Q

@csrf_exempt
@api_safe_json_response
def triagings(request, id):
    result = None
    if request.method == "POST":
        pass

    elif request.method == "GET":
        q = Q()
        if id:
            q = q & Q(execution_id=id)
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
                          "build_parameters": triage.build_parameters}
            result.append(one_record)
    return result


@csrf_exempt
@api_safe_json_response
def triaging_states(request):
    return TriagingStates().all_codes_to_string()


@csrf_exempt
@api_safe_json_response
def triaging_trial_states(request):
    return TriageTrialStates().all_codes_to_string()