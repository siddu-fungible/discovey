from fun_global import get_current_time
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed
from django.db.models import Q
from web.fun_test.models import SuiteExecution, TestCaseExecution, TestbedNotificationEmails
from web.fun_test.models import ScriptInfo, RegresssionScripts
from fun_settings import TEAM_REGRESSION_EMAIL
import json
from lib.utilities.send_mail import send_mail
from datetime import datetime, timedelta
from scheduler.scheduler_global import JobStatusType
from scheduler.scheduler_helper import kill_job
from asset.asset_global import AssetType
from asset.asset_manager import AssetManager

@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    am = AssetManager()
    if request.method == "GET":
        if not id:
            all_test_beds = TestBed.objects.all().order_by('name')
            result = []
            for test_bed in all_test_beds:
                t = {"name": test_bed.name,
                     "description": test_bed.description,
                     "id": test_bed.id,
                     "manual_lock": test_bed.manual_lock,
                     "manual_lock_expiry_time": str(test_bed.manual_lock_expiry_time),
                     "manual_lock_submitter": test_bed.manual_lock_submitter}
                if not test_bed.manual_lock:
                    asset_level_manual_locked, error_message, manual_lock_user, assets_required = am.check_test_bed_manual_locked(
                        test_bed_name=test_bed.name)
                    t["asset_level_manual_lock_status"] = {"asset_level_manual_locked": asset_level_manual_locked,
                                                           "error_message": error_message,
                                                           "asset_level_manual_lock_user": manual_lock_user}
                result.append(t)

        else:
            t = TestBed.objects.get(name=id)
            result = {"name": t.name,
                      "description": t.description,
                      "id": t.id,
                      "manual_lock": t.manual_lock,
                      "manual_lock_expiry_time": str(t.manual_lock_expiry_time),
                      "manual_lock_submitter": t.manual_lock_submitter}
            test_bed_availability = am.get_test_bed_availability(test_bed_type=t.name)
            if not t.manual_lock:
                asset_level_manual_locked, error_message, manual_lock_user, assets_required = am.check_test_bed_manual_locked(
                    test_bed_name=t.name)
                result["asset_level_manual_lock_status"] = {"asset_level_manual_locked": asset_level_manual_locked,
                                                            "error_message": error_message,
                                                            "asset_level_manual_lock_user": manual_lock_user}

            result["automation_status"] = test_bed_availability

    if request.method == "PUT":
        test_bed = TestBed.objects.get(id=int(id))
        request_json = json.loads(request.body)

        extension_hour = None
        extension_minute = None
        submitter_email = None
        if "manual_lock_extension_hour" in request_json:
            extension_hour = request_json["manual_lock_extension_hour"]
        if "manual_lock_extension_minute" in request_json:
            extension_minute = request_json["manual_lock_extension_minute"]
        if "manual_lock_submitter_email" in request_json:
            submitter_email = request_json["manual_lock_submitter_email"]
            test_bed.manual_lock_submitter = submitter_email


        this_is_extension_request = False
        if extension_hour is not None and extension_minute is not None:
            future_time = get_current_time() + timedelta(hours=int(extension_hour),
                                                         minutes=int(extension_minute))
            this_is_extension_request = True
            test_bed.manual_lock_expiry_time = future_time
        if "manual_lock" in request_json:
            test_bed.manual_lock = request_json["manual_lock"]

        if test_bed.manual_lock:
            manual_locked, error_message, manual_lock_user, assets_required = am.check_test_bed_manual_locked(test_bed_name=test_bed.name)
            if manual_locked and not this_is_extension_request:
                raise Exception(error_message)
            else:
                if submitter_email:
                    am.manual_lock_assets(user=submitter_email, assets=assets_required)
                else:
                    pass  # TODO
        else:
            am.manual_un_lock_assets_by_test_bed(test_bed_name=test_bed.name, user=test_bed.manual_lock_submitter)

        test_bed.save()

        if test_bed.manual_lock_submitter:

            default_email_list = [x.email for x in TestbedNotificationEmails.objects.all()]
            to_addresses = [test_bed.manual_lock_submitter]
            to_addresses.extend(default_email_list)

            lock_or_unlock = "lock" if test_bed.manual_lock else "un-lock"
            subject = "Manual {} for Test-bed: {} User: {} ".format(lock_or_unlock, test_bed.name, test_bed.manual_lock_submitter)
            content = subject
            send_mail(to_addresses=to_addresses, subject=subject, content=content)
        pass
    return result

@csrf_exempt
@api_safe_json_response
def suite_executions(request, id):
    result = None
    if request.method == "DELETE":
        suite_execution = SuiteExecution.objects.get(execution_id=int(id))
        kill_job(job_id=int(id))
        suite_execution.delete()
        test_case_executions = TestCaseExecution.objects.filter(suite_execution_id=int(id))
        test_case_executions.delete()

        result = True

    if request.method == "GET":
        q = Q()
        test_bed_type = request.GET.get('test_bed_type', None)
        if test_bed_type:
            q = q & Q(test_bed_type=test_bed_type)
        state = request.GET.get('state', None)
        if state:
            q = q & Q(state=int(state))
        if id:
            q = q & Q(execution_id=id)

        is_completed = request.GET.get('is_job_completed', None) # used by qa_trigger.py

        records = []
        suite_executions = SuiteExecution.objects.filter(q).order_by('submitted_time')
        for suite_execution in suite_executions:
            one_record = {"execution_id": suite_execution.execution_id,
                          "state": suite_execution.state,
                          "result": suite_execution.result,
                          "environment": json.loads(suite_execution.environment)}
            records.append(one_record)
            if id is not None:
                result = one_record
                break
        result = records if len(records) else None
        if is_completed:
            if records:
                first_record = records[0]
                result = {"result": first_record["result"],
                          "is_completed": JobStatusType.is_completed(first_record["state"]),
                          "job_state_code": first_record["state"],
                          "job_state_string": JobStatusType().code_to_string(first_record["state"]),
                          "message": "State is {}".format(JobStatusType().code_to_string(first_record["state"]))}
            else:
                result = {"result": "FAILED",
                          "is_completed": True,
                          "job_state_code": JobStatusType.ERROR,
                          "job_state_string": JobStatusType().code_to_string(JobStatusType.ERROR),
                          "message": "Job-id: {} does not exist".format(id)}

    return result


@csrf_exempt
@api_safe_json_response
def script_infos(request, pk):
    result = None
    if request.method == 'GET':
        q = Q()
        if pk:
            q = q & Q(script_id=int(pk))
        script_infos = ScriptInfo.objects.filter(q)
        result = []
        for script_info in script_infos:
            regression_script = RegresssionScripts.objects.get(pk=script_info.pk)

            result.append({"id": script_info.script_id,
                           "bug": script_info.bug,
                           "pk": script_info.pk,
                           "script_path": regression_script.script_path})
    return result
