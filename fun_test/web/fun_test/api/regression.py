from fun_global import get_current_time
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed, Asset
from django.db.models import Q
from web.fun_test.models import SuiteExecution, TestCaseExecution, TestbedNotificationEmails
from web.fun_test.models import ScriptInfo, RegresssionScripts
from fun_settings import TEAM_REGRESSION_EMAIL, SCRIPTS_DIR
import json
from lib.utilities.send_mail import send_mail
from datetime import datetime, timedelta
from scheduler.scheduler_global import JobStatusType
from scheduler.scheduler_helper import kill_job
from django.core.exceptions import ObjectDoesNotExist
from asset.asset_global import AssetType
from web.fun_test.models import Module
from web.fun_test.fun_serializer import model_instance_to_dict
from web.fun_test.models_helper import _get_suite_executions
from fun_global import RESULTS
import os
import fnmatch



@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    from asset.asset_manager import AssetManager
    am = AssetManager()
    if request.method == "GET":
        if not id:
            valid_test_beds = am.get_valid_test_beds()
            all_test_beds = TestBed.objects.all().order_by('name')
            all_test_beds = [x for x in all_test_beds if x.name in valid_test_beds]
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
                test_bed_availability = am.get_test_bed_availability(test_bed_type=test_bed.name)
                t["automation_status"] = test_bed_availability
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
        description = None
        if "manual_lock_extension_hour" in request_json:
            extension_hour = request_json["manual_lock_extension_hour"]
        if "manual_lock_extension_minute" in request_json:
            extension_minute = request_json["manual_lock_extension_minute"]
        if "manual_lock_submitter_email" in request_json:
            submitter_email = request_json["manual_lock_submitter_email"]
            test_bed.manual_lock_submitter = submitter_email
        if "description" in request_json:
            test_bed.description = request_json["description"]
        if "note" in request_json:
            test_bed.note = request_json["note"]

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
                #raise Exception(error_message)
                pass
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
        suite_path = request.GET.get('suite_path', None)
        if suite_path:
            q = q & Q(suite_path=suite_path)
        test_bed_type = request.GET.get('test_bed_type', None)
        if test_bed_type:
            q = q & Q(test_bed_type=test_bed_type)
        state = request.GET.get('state', None)
        if state:
            q = q & Q(state=int(state))
        if id:
            q = q & Q(execution_id=id)
        order_by = request.GET.get('order_by', None)
        if order_by:
            suite_execution_objects = SuiteExecution.objects.filter(q).exclude(started_time=None).order_by(order_by)
        else:
            suite_execution_objects = SuiteExecution.objects.filter(q).order_by('submitted_time')

        is_completed = request.GET.get('is_job_completed', None) # used by qa_trigger.py

        records = []
        for suite_execution in suite_execution_objects:
            one_record = {"execution_id": suite_execution.execution_id,
                          "state": suite_execution.state,
                          "result": suite_execution.result,
                          "environment": json.loads(suite_execution.environment),
                          "suite_path": suite_execution.suite_path,
                          "started_time": suite_execution.started_time,
                          "completed_time": suite_execution.completed_time}
            records.append(one_record)
            if id:
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

    if request.method == "PUT":
        try:
            suite_execution = SuiteExecution.objects.get(execution_id=int(id))
            request_json = json.loads(request.body)
            if "disable_schedule" in request_json:
                suite_execution.disable_schedule = request_json["disable_schedule"]
            suite_execution.save()
        except ObjectDoesNotExist:
            # TODO
            pass
    return result

@csrf_exempt
@api_safe_json_response
def test_case_executions(request, id):
    if request.method == 'GET':
        suite_id = request.GET.get("suite_id", None)
        test_executions = TestCaseExecution.objects.filter(suite_execution_id=int(suite_id))
        num_passed = 0
        num_failed = 0
        for test_execution in test_executions:
            if test_execution.result == RESULTS["PASSED"]:
                num_passed += 1
            elif test_execution.result == RESULTS["FAILED"]:
                num_failed += 1
        return {"num_passed": num_passed, "num_failed": num_failed}



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


"""
    name = models.TextField(unique=True)
    type = models.TextField()
    job_ids = JSONField(default=[])
    manual_lock_user = models.TextField(default=None, null=True)
"""

@csrf_exempt
@api_safe_json_response
def assets(request, name, asset_type):
    result = None
    if request.method == "GET":
        if not name:
            all_assets = Asset.objects.all()
            result = []
            for one_asset in all_assets:
                one_record = {"name": one_asset.name,
                              "type": one_asset.type,
                              "manual_lock_user": one_asset.manual_lock_user,
                              "job_ids": one_asset.job_ids,
                              "test_beds": one_asset.test_beds}
                result.append(one_record)
    elif request.method == "PUT":
        request_json = json.loads(request.body)
        try:
            asset = Asset.objects.get(name=name, type=asset_type)
            original_manual_lock_user = asset.manual_lock_user
            if "manual_lock_user" in request_json:
                asset.manual_lock_user = request_json.get("manual_lock_user")
                lock_or_unlock = "lock" if asset.manual_lock_user else "un-lock"
                to_addresses = [TEAM_REGRESSION_EMAIL]
                if original_manual_lock_user:
                    to_addresses.append(original_manual_lock_user)
                    if (original_manual_lock_user != asset.manual_lock_user) and asset.manual_lock_user:
                        to_addresses.append(asset.manual_lock_user)
                send_mail(to_addresses=to_addresses, subject="{} {}".format(asset.name, lock_or_unlock))
            asset.save()
            result = True
        except Exception as ex:
            pass #TODO
    return result


@csrf_exempt
@api_safe_json_response
def categories(request):
    result = []
    all_categories = Module.objects.all().order_by('name')
    for category in all_categories:
        result.append(model_instance_to_dict(category))
    return result

@csrf_exempt
@api_safe_json_response
def sub_categories(request):
    pass

@csrf_exempt
@api_safe_json_response
def asset_types(request):
    return AssetType().all_strings_to_code()


def _fix_missing_scripts():
    missing_scripts = []
    for root, dir_names, file_names in os.walk(SCRIPTS_DIR):
        for file_name in fnmatch.filter(file_names, '*.py'):
            full_path = os.path.join(root, file_name)
            try:
                f = open(full_path, "r")
                contents = f.read()
                if "if __name__ == \"__main__\"" in contents:
                    relative_path = full_path.replace(SCRIPTS_DIR, "")
                    if not RegresssionScripts.objects.filter(script_path=relative_path).exists():
                        missing_scripts.append(relative_path)

            except:
                pass  # TODO

    for missing_script in missing_scripts:
        module = "general"
        if "accelerators" in missing_script:
            module = "accelerators"
        if "security" in missing_script:
            module = "security"
        if "networking" in missing_script:
            module = "networking"
        if "system" in missing_script:
            module = "system"
        print module, missing_script
        RegresssionScripts(script_path=missing_script, modules=json.dumps([module])).save()


@csrf_exempt
@api_safe_json_response
def scripts(request):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        operation = request_json.get("operation", None)
        if operation == "fix_missing_scripts":
            _fix_missing_scripts()
            result = True
    return result


if __name__ == "__main__":
    from web.fun_test.django_interactive import *
    print categories(None)