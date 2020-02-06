from fun_global import get_current_time, get_epoch_time_from_datetime
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed, Asset
from django.db.models import Q
from web.fun_test.models import SuiteExecution, TestCaseExecution, TestbedNotificationEmails, LastSuiteExecution
from web.fun_test.models import ScriptInfo, RegresssionScripts, SuiteReRunInfo, TestCaseInfo
from web.fun_test.models import ReleaseCatalog, SavedJobConfig
from scheduler.scheduler_global import SchedulingType
from scheduler.scheduler_global import SchedulerStates
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
from web.fun_test.models_helper import _get_suite_executions, get_fun_test_time_series_collection_name
from web.fun_test.models_helper import get_ts_test_case_context_info_collection_name
from web.fun_test.models_helper import get_ts_script_run_time_collection_name
from scheduler.scheduler_global import SuiteType
from web.fun_test.models import Suite
from fun_global import RESULTS
from django.core import paginator
import os
import fnmatch
from fun_settings import MAIN_WEB_APP
from django.apps import apps
from bson import json_util
from web.fun_test.models_helper import get_script_id
from fun_global import TimeSeriesTypes
from web.fun_test.models import ReleaseCatalogExecution
import time
import datetime
from asset.asset_global import AssetHealthStates

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    from asset.asset_manager import AssetManager
    am = AssetManager()
    if request.method == "GET":
        minimal = request.GET.get("minimal", False)
        name = request.GET.get("name", None)

        if not id:
            valid_test_beds = am.get_valid_test_beds()
            if name:
                all_test_beds = TestBed.objects.filter(name=name)
            else:
                all_test_beds = TestBed.objects.all().order_by('name')

            all_test_beds = [x for x in all_test_beds if x.name in valid_test_beds]
            result = []

            all_test_bed_specs = None
            for test_bed in all_test_beds:
                t = {"name": test_bed.name,
                     "description": test_bed.description,
                     "id": test_bed.id,
                     "note": test_bed.note,
                     "manual_lock": test_bed.manual_lock,
                     "manual_lock_expiry_time": str(test_bed.manual_lock_expiry_time),
                     "manual_lock_submitter": test_bed.manual_lock_submitter,
                     "health_status": test_bed.health_status,
                     "disabled": test_bed.disabled,
                     "health_check_message": test_bed.health_check_message,
                     "health_check_enabled": test_bed.health_check_enabled}
                if not minimal:
                    if not test_bed.manual_lock:
                        if not all_test_bed_specs:
                            all_test_bed_specs = am.get_all_test_beds_specs()
                        asset_level_manual_locked, error_message, manual_lock_user, assets_required = am.check_test_bed_manual_locked(
                            test_bed_name=test_bed.name, all_test_bed_specs=all_test_bed_specs)

                        t["asset_level_manual_lock_status"] = {"asset_level_manual_locked": asset_level_manual_locked,
                                                               "error_message": error_message,
                                                               "asset_level_manual_lock_user": manual_lock_user}

                    test_bed_availability = am.get_test_bed_availability(test_bed_type=test_bed.name,
                                                                         all_test_bed_specs=all_test_bed_specs)

                    t["automation_status"] = test_bed_availability

                result.append(t)

        else:
            t = TestBed.objects.get(name=id)
            result = {"name": t.name,
                      "description": t.description,
                      "id": t.id,
                      "note": t.note,
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
        if "disabled" in request_json:
            test_bed.disabled = request_json["disabled"]
        if "health_check_enabled" in request_json:
            test_bed.health_check_enabled = request_json["health_check_enabled"]

        this_is_extension_request = False
        if extension_hour is not None and extension_minute is not None:
            future_time = get_current_time() + timedelta(hours=int(extension_hour),
                                                         minutes=int(extension_minute))
            this_is_extension_request = True
            test_bed.manual_lock_expiry_time = future_time
        if "manual_lock" in request_json:
            test_bed.manual_lock = request_json["manual_lock"]

        if test_bed.manual_lock:
            manual_locked, error_message, manual_lock_user, assets_required = am.check_test_bed_manual_locked(
                test_bed_name=test_bed.name)
            if manual_locked and not this_is_extension_request:
                # raise Exception(error_message)
                pass
            else:
                if submitter_email:
                    am.manual_lock_assets(user=submitter_email, assets=assets_required,
                                          expiration_time=test_bed.manual_lock_expiry_time)
                else:
                    pass  # TODO
        else:
            test_bed.note = ""
            am.manual_un_lock_assets_by_test_bed(test_bed_name=test_bed.name, user=test_bed.manual_lock_submitter)

        test_bed.save()

        if test_bed.manual_lock_submitter:
            default_email_list = [x.email for x in TestbedNotificationEmails.objects.all()]
            to_addresses = [test_bed.manual_lock_submitter]
            to_addresses.extend(default_email_list)

            lock_or_unlock = "lock" if test_bed.manual_lock else "un-lock"
            subject = "Manual {} for Test-bed: {} User: {} ".format(lock_or_unlock, test_bed.name,
                                                                    test_bed.manual_lock_submitter)
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

        is_completed = request.GET.get('is_job_completed', None)  # used by qa_trigger.py

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
                scheduled_suites = SuiteExecution.objects.filter(auto_scheduled_execution_id=int(id),
                                                                 state=JobStatusType.SCHEDULED)
                for scheduled_suite in scheduled_suites:
                    scheduled_suite.delete()
            if "preserve_logs" in request_json:
                suite_execution.preserve_logs = request_json["preserve_logs"]
            if "pause_on_failure" in request_json:
                suite_execution.pause_on_failure = request_json["pause_on_failure"]
            suite_execution.save()
        except ObjectDoesNotExist:
            # TODO
            pass
    return result


@csrf_exempt
@api_safe_json_response
def test_case_executions(request, id):
    if request.method == 'GET':
        suite_execution_id = request.GET.get("suite_execution_id", None)
        q = Q()
        if suite_execution_id:
            q = q & Q(suite_execution_id=int(suite_execution_id))
        script_path = request.GET.get("script_path", None)
        if script_path:
            q = q & Q(script_path=script_path)

        log_prefix = request.GET.get("log_prefix", None)
        if log_prefix is not None:
            q = q & Q(log_prefix=log_prefix)
        test_executions = TestCaseExecution.objects.filter(q).order_by("started_time")
        results = []
        for test_execution in test_executions:
            summary = "Unknown"
            if test_execution.test_case_id == 0:
                summary = "Script setup"
            elif test_execution.test_case_id == 999:
                summary = "Script cleanup"
            else:
                try:
                    test_case_info = TestCaseInfo.objects.get(test_case_id=test_execution.test_case_id,
                                                              script_path=test_execution.script_path)
                    summary = test_case_info.summary
                except ObjectDoesNotExist:
                    pass
            results.append({"result": test_execution.result,
                            "test_case_id": test_execution.test_case_id,
                            "suite_execution_id": test_execution.suite_execution_id,
                            "execution_id": test_execution.execution_id,
                            "summary": summary,
                            "started_epoch_time": get_epoch_time_from_datetime(test_execution.started_time) / 1000})
        return results


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
            try:
                regression_script = RegresssionScripts.objects.get(pk=script_info.pk)

                result.append({"id": script_info.script_id,
                               "bug": script_info.bug,
                               "pk": script_info.pk,
                               "script_path": regression_script.script_path})
            except Exception as ex:
                pass
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
        test_bed_name = request.GET.get("test_bed_name", None)
        if not name:
            if not test_bed_name:
                all_assets = Asset.objects.all()
            else:
                all_assets = Asset.objects.filter(test_beds__contains=test_bed_name)
            result = []
            for one_asset in all_assets:
                one_record = {"name": one_asset.name,
                              "type": one_asset.type,
                              "manual_lock_user": one_asset.manual_lock_user,
                              "job_ids": one_asset.job_ids,
                              "test_beds": one_asset.test_beds,
                              "manual_lock_expiry_time": one_asset.manual_lock_expiry_time,
                              "disabled": one_asset.disabled,
                              "health_status": one_asset.health_status,
                              "health_check_enabled": one_asset.health_check_enabled,
                              "health_check_message": one_asset.health_check_message}
                result.append(one_record)
    elif request.method == "PUT":
        request_json = json.loads(request.body)
        try:
            asset = Asset.objects.get(name=name, type=asset_type)

            original_manual_lock_user = asset.manual_lock_user
            if "manual_lock_user" in request_json:
                associated_test_beds = asset.test_beds
                if request_json.get("manual_lock_user", None) and associated_test_beds:
                    for associated_test_bed in associated_test_beds:
                        try:
                            associated_test_bed_object = TestBed.objects.get(name=associated_test_bed)
                            if associated_test_bed_object.manual_lock and associated_test_bed_object.manual_lock_submitter:
                                raise Exception(
                                    "Asset: {} is already locked at the Test-bed: {} level".format(asset.name,
                                                                                                   associated_test_bed_object.name))
                        except ObjectDoesNotExist:
                            pass

                asset.manual_lock_user = request_json.get("manual_lock_user")
                lock_or_unlock = "lock" if asset.manual_lock_user else "un-lock"
                to_addresses = [TEAM_REGRESSION_EMAIL]
                if original_manual_lock_user or asset.manual_lock_user:
                    to_addresses.append(original_manual_lock_user)
                    if (original_manual_lock_user != asset.manual_lock_user) and asset.manual_lock_user:
                        to_addresses.append(asset.manual_lock_user)
                send_mail(to_addresses=to_addresses, subject="{} {}".format(asset.name, lock_or_unlock))
            if "disabled" in request_json:
                asset.disabled = request_json["disabled"]
            if "health_check_enabled" in request_json:
                asset.health_check_enabled = request_json["health_check_enabled"]
            if "minutes" in request_json:
                asset.manual_lock_expiry_time = get_current_time() + timedelta(minutes=int(request_json["minutes"]))
            asset.save()
            result = True
        except Exception as ex:
            raise Exception(str(ex))
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
                if "if __name__ == \"__main__\"" or "if __name__ == '__main__'" in contents:
                    relative_path = full_path.replace(SCRIPTS_DIR, "")
                    if not RegresssionScripts.objects.filter(script_path=relative_path).exists():
                        missing_scripts.append(relative_path)

            except Exception as ex:
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
def scripts(request, id):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        operation = request_json.get("operation", None)
        if operation == "fix_missing_scripts":
            _fix_missing_scripts()
            result = True
    if request.method == "GET":
        q = Q()
        if id is not None:
            q &= Q(id=int(id))
        regression_scripts = RegresssionScripts.objects.filter(q)
        result = []
        for script in regression_scripts:
            result.append({"script_path": script.script_path, "id": script.id})
        if result and id is not None:
            result = result[0]
    return result


@csrf_exempt
@api_safe_json_response
def suites(request, id):
    result = None
    if request.method == "GET":
        if not id:
            get_count = request.GET.get("get_count", None)
            q = Q()
            categories = request.GET.get("categories", None)
            if categories is not None:
                categories = categories.split(",")
                for category in categories:
                    q &= Q(categories__contains=category)
            search_by_name_text = request.GET.get("search_by_name", None)
            if search_by_name_text:
                q &= Q(name__icontains=search_by_name_text)
            all_suites = Suite.objects.filter(q).extra(select={'case_insensitive_name': 'lower(name)'}).order_by(
                'case_insensitive_name')
            if get_count is None:
                records_per_page = request.GET.get("records_per_page", None)
                page = request.GET.get("page", None)
                if records_per_page is not None:
                    p = paginator.Paginator(all_suites, records_per_page)
                    all_suites = p.page(page)
                    result = []
                    for suite in all_suites:
                        result.append(suite.to_dict())

            else:
                result = all_suites.count()
        else:
            id = int(id)
            result = Suite.objects.get(id=id).to_dict()

    if request.method == "POST":
        if not id:
            s = Suite()
        else:
            s = Suite.objects.get(id=id)
        request_json = json.loads(request.body)
        name = request_json.get("name", None)
        short_description = request_json.get("short_description", None)
        categories = request_json.get("categories", None)
        tags = request_json.get("tags", None)
        custom_test_bed_spec = request_json.get("custom_test_bed_spec", None)
        suite_entries = request_json.get("entries", None)
        type = request_json.get("type", "SUITE")  # TODO
        s.type = type
        s.name = name
        s.short_description = short_description
        s.categories = categories
        s.tags = tags
        s.custom_test_bed_spec = custom_test_bed_spec
        if suite_entries is not None:
            s.entries = suite_entries
        s.save()

    if request.method == "DELETE":
        s = Suite.objects.get(id=id)
        s.delete()
        result = True
    return result


@csrf_exempt
@api_safe_json_response
def re_run_job(request):
    if request.method == "POST":
        request_json = json.loads(request.body)
        original_suite_execution_id = request_json.get("original_suite_execution_id", None)
        script_filter = request_json.get("script_filter", None)
        result_filter = request_json.get("result_filter", None)
        test_case_executions = TestCaseExecution.objects.filter(suite_execution_id=original_suite_execution_id)
        re_run_info = {}
        for test_case_execution in test_case_executions:
            script_id = get_script_id(test_case_execution_id=test_case_execution.execution_id)
            if script_filter:
                if script_id and script_id != script_filter:
                    continue

            if result_filter and (test_case_execution.result not in result_filter):
                continue

            log_prefix = int(test_case_execution.log_prefix)
            if log_prefix not in re_run_info:
                re_run_info[log_prefix] = {}
            re_run_info[log_prefix][test_case_execution.test_case_id] = {
                "test_case_execution_id": test_case_execution.execution_id}
        suite_id = request_json.get("suite_id", None)
        re_use_build_image = request_json.get("re_use_build_image", None)
        original_suite_execution = SuiteExecution.objects.get(execution_id=original_suite_execution_id)

        original_environment = None
        try:
            original_environment = json.loads(original_suite_execution.environment)
        except:
            pass
        if original_environment:
            with_jenkins_build = original_environment.get("with_jenkins_build", None)
            if with_jenkins_build:
                tftp_image_path = original_environment.get("tftp_image_path", None)
                if tftp_image_path and not re_use_build_image:
                    del original_environment["tftp_image_path"]

        new_suite_execution = original_suite_execution
        new_suite_execution.environment = json.dumps(original_environment)
        new_suite_execution.pk = None
        new_suite_execution.build_done = False
        new_suite_execution.execution_id = LastSuiteExecution.get_next()
        new_suite_execution.submitted_time = get_current_time()
        new_suite_execution.scheduled_time = get_current_time()
        new_suite_execution.completed_time = get_current_time()
        new_suite_execution.started_time = get_current_time()
        new_suite_execution.result = RESULTS["UNKNOWN"]
        new_suite_execution.finalized = False
        new_suite_execution.preserve_logs = False
        new_suite_execution.state = JobStatusType.SUBMITTED
        new_suite_execution.run_time = {}
        new_suite_execution.assets_used = None
        new_suite_execution.test_case_execution_ids = json.dumps([])
        new_suite_execution.is_re_run = True
        new_suite_execution.re_run_info = re_run_info
        new_suite_execution.suite_type = SuiteType.DYNAMIC
        new_suite_execution.scheduling_type = SchedulingType.ASAP
        new_suite_execution.save()

        SuiteReRunInfo(original_suite_execution_id=original_suite_execution_id,
                       re_run_suite_execution_id=new_suite_execution.execution_id).save()

        if suite_id:
            pass


@api_safe_json_response
def test_case_time_series(request, suite_execution_id):
    result = None
    if request.method == "GET":
        type = request.GET.get("type", None)
        checkpoint_index = request.GET.get("checkpoint_index", None)
        collection_name = get_fun_test_time_series_collection_name(
            suite_execution_id)  # "s_{}_{}".format(suite_execution_id, test_case_execution_id)
        mongo_db_manager = app_config.get_mongo_db_manager()
        collection = mongo_db_manager.get_collection(collection_name)

        start_epoch = request.GET.get("start_epoch", None)
        end_epoch = request.GET.get("end_epoch", None)

        min_checkpoint_index = request.GET.get("min_checkpoint_index", None)
        max_checkpoint_index = request.GET.get("max_checkpoint_index", None)
        query = {}
        if type:
            type = int(type)
            query["type"] = type

        if type is not None:
            if type == TimeSeriesTypes.LOG:
                query["type"] = {"$or": [TimeSeriesTypes.LOG, TimeSeriesTypes.CHECKPOINT]}
        test_case_execution_id = request.GET.get("test_case_execution_id", None)
        if test_case_execution_id is not None:
            query["te"] = int(test_case_execution_id)
        if checkpoint_index is not None:
            query["data.checkpoint_index"] = int(checkpoint_index)
        t = request.GET.get("t", None)  # sub-type like statistics type
        if t is not None:
            query["t"] = int(t)

        asset_id = request.GET.get("asset_id", None)
        if asset_id is not None:
            query["asset_id"] = asset_id

        epoch_filter = {}
        if start_epoch is not None:
            epoch_filter["$gte"] = start_epoch
        if end_epoch is not None:
            epoch_filter["$lte"] = end_epoch
        if epoch_filter:
            query["epoch_time"] = epoch_filter

        checkpoint_filter = {}
        if max_checkpoint_index is not None:
            checkpoint_filter["$lte"] = int(max_checkpoint_index)
        if min_checkpoint_index is not None:
            checkpoint_filter["$gte"] = int(min_checkpoint_index)
        if checkpoint_filter:
            query["data.checkpoint_index"] = checkpoint_filter

        if collection:
            result = list(collection.find(query).sort('epoch_time'))
    return result


@api_safe_json_response
def contexts(request, suite_execution_id, script_id):
    result = None
    if request.method == "GET":
        collection_name = get_fun_test_time_series_collection_name(suite_execution_id)
        mongo_db_manager = app_config.get_mongo_db_manager()
        collection = mongo_db_manager.get_collection(collection_name)
        query = {"type": TimeSeriesTypes.CONTEXT_INFO}
        if collection:
            if script_id:
                query["script_id"] = int(script_id)
            if suite_execution_id:
                query["suite_execution_id"] = int(suite_execution_id)
            result = list(collection.find(query))
    return result


@api_safe_json_response
def script_run_time(request, suite_execution_id, script_id):
    result = None
    if request.method == "GET":
        collection_name = get_fun_test_time_series_collection_name(suite_execution_id)
        mongo_db_manager = app_config.get_mongo_db_manager()
        collection = mongo_db_manager.get_collection(collection_name)
        query = {}
        if collection:
            query["type"] = TimeSeriesTypes.SCRIPT_RUN_TIME
            if script_id:
                query["script_id"] = int(script_id)
            if suite_execution_id:
                query["suite_execution_id"] = int(suite_execution_id)
            result = json.loads(json_util.dumps(collection.find_one(query)))
    return result


@api_safe_json_response
def release_trains(request):
    releases = ["master", "1.0a_aa", "1.0a_ab"]
    result = None
    if request.method == "GET":
        result = releases
    return result


@csrf_exempt
@api_safe_json_response
def release_catalogs(request, catalog_id):
    result = None
    if request.method == "GET":
        q = Q()
        if catalog_id:
            q = q & Q(id=int(catalog_id))
        catalog_objects = ReleaseCatalog.objects.filter(q)
        result = []
        for catalog_object in catalog_objects:
            if catalog_id:
                result = catalog_object.to_dict()
                break
            else:
                result.append(catalog_object.to_dict())

    elif request.method == "POST":
        request_json = json.loads(request.body)
        request_json["created_date"] = get_current_time()
        c = ReleaseCatalog(**request_json)
        c.save()
        result = c.id
    elif request.method == "DELETE":
        if catalog_id:
            try:
                c = ReleaseCatalog.objects.get(id=int(catalog_id))
                c.delete()
            except ObjectDoesNotExist:
                pass

        pass
    elif request.method == "PUT":
        if catalog_id:
            try:
                c = ReleaseCatalog.objects.get(id=int(catalog_id))
                request_json = json.loads(request.body)
                for key, value in request_json.iteritems():
                    setattr(c, key, value)
                    c.save()
            except ObjectDoesNotExist:
                pass
    return result


@api_safe_json_response
def time_series_types(request):
    result = None
    if request.method == "GET":
        result = TimeSeriesTypes().all_strings_to_code()
    return result


@api_safe_json_response
def job_status_types(request):
    result = None
    if request.method == "GET":
        result = {}
        result["string_code_map"] = JobStatusType().all_strings_to_code()
        result["code_description_map"] = JobStatusType().get_code_to_description_map()
    return result


@csrf_exempt
@api_safe_json_response
def release_catalog_executions(request, id):
    result = None
    if request.method == "POST":
        request_json = json.loads(request.body)
        if not id:
            release_train = request_json.get("release_train")
            description = request_json.get("description")
            if ReleaseCatalogExecution.objects.filter(release_train=release_train, description=description).count() > 0:
                raise Exception("This description has already been taken")

            execution = ReleaseCatalogExecution(**request_json)
            execution.save()
            result = execution.to_dict()

    if request.method == "GET":
        q = Q()
        if id:
            q = q & Q(id=int(id))
        executions = ReleaseCatalogExecution.objects.filter(q).order_by('-started_date')
        if executions.count():
            if not id:
                result = map(lambda x: x.to_dict(), executions)
            else:
                result = executions[0].to_dict()
    if request.method == "PUT":
        request_json = json.loads(request.body)
        q = Q(id=int(id))
        execution = ReleaseCatalogExecution.objects.get(q)

        for key, value in request_json.iteritems():
            if key == "ready_for_execution":
                if not execution.ready_for_execution and value:
                    execution.state = JobStatusType.SUBMITTED
            if key == "suite_executions":
                for suite_execution_entry in value:
                    if "re_run_request" in suite_execution_entry and suite_execution_entry["re_run_request"]:
                        suite_execution_entry["re_run_request"] = False
                        suite_execution_entry["re_run_request_submitted"] = True
                        execution.state = JobStatusType.IN_PROGRESS
                        execution.result = RESULTS["UNKNOWN"]
            if hasattr(execution, key):
                setattr(execution, key, value)

        execution.save()
        result = execution.to_dict()

    if request.method == "DELETE":
        q = Q(id=int(id))
        execution = ReleaseCatalogExecution.objects.get(q)
        if execution:
            execution.deleted = True
            execution.save()
        result = True
    return result


@csrf_exempt
@api_safe_json_response
def saved_configs(request, id):
    result = None
    if request.method == "GET":
        if id:
            id = int(id)
            saved_job_config = SavedJobConfig.objects.get(id=id)
            result = saved_job_config.to_dict()
    if request.method == "POST":
        request_json = json.loads(request.body)
        execution = SavedJobConfig(**request_json)
        execution.save()
        result = execution.to_dict()
    return result


@api_safe_json_response
def asset_health_states(request):
    result = None
    if request.method == "GET":
        result = AssetHealthStates().get_maps()
    return result


if __name__ == "__main__":
    from web.fun_test.django_interactive import *

    print categories(None)
