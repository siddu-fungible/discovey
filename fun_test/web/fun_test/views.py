import json
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.jira_manager import JiraManager
from lib.utilities.script_fixup import fix
from fun_global import *
from fun_settings import TCMS_PROJECT

@csrf_exempt
def publish(request):
    logs = []
    response = {}
    response["status"] = RESULT_FAIL
    if request.method == 'POST':
        request_json = json.loads(request.body)

        test_case_id = request_json["id"]
        test_case_summary = request_json["summary"]
        test_case_steps = request_json["steps"]
        setup_summary = request_json["setup_summary"]
        setup_steps = request_json["setup_steps"]
        full_script_path = request_json["full_script_path"]
        if str(test_case_id) in [str(0), str(999)]:  #TODO: hardcoded 999
            response["status"] = RESULT_PASS
        else:
            jira_manager = JiraManager()
            jira_summary = test_case_summary
            jira_description = "Setup:\n{}\n{}\n\n\nTest:\n{}\n{}\n".format(setup_summary,
                                                                        setup_steps,
                                                                        test_case_summary,
                                                                        test_case_steps)

            if test_case_id == "$tc":  #TODO: make this global
                result = jira_manager.generate_issue()

                if not result["status"]  == RESULT_PASS:
                    response["status"] = RESULT_FAIL
                    logs.append(result["err_msg"])
                else:
                    response["status"] = RESULT_PASS
                    test_case_id = result["issue_id"]
                    logs.append("Fetched JIRA {}-{}".format(TCMS_PROJECT, test_case_id))
                    fix(script_path=full_script_path, id=test_case_id)
            jira_manager.update_test_case(id=test_case_id, summary=jira_summary, description=jira_description)  #TODO: what about an error here?
            logs.append("Updated Test-case: {}".format(test_case_id))
    response["logs"] = logs
    return HttpResponse(json.dumps(response))

@csrf_exempt
def get_script_content(request):
    contents = "Could not find script"
    if request.method == 'POST':
        try:
            request_json = json.loads(request.body)
            full_script_path = request_json["full_script_path"]
            f = open(full_script_path, "r")
            contents = f.read()
            f.close()
        except Exception as ex:
            contents = str(ex)
    return HttpResponse(contents)

@csrf_exempt
def angular_home(request):
    return render(request, 'qa_dashboard/upgrade.html', locals())

def index(request):
    request.session.clear()
    return render(request, 'base.html', locals())