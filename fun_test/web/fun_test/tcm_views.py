from fun_settings import TCMS_PROJECT
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
import logging, json
from web.fun_test.tcm_common import CATALOG_CATEGORIES
from web_global import initialize_result
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.jira_manager import JiraManager
from web.fun_test.models import CatalogSuite, CatalogTestCase, CatalogSuiteExecution, CatalogTestCaseExecution
from web.fun_test.models import TestBed, Engineer, TestCaseExecution
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic
from web.fun_test.models_helper import add_suite_execution, add_test_case_execution
from fun_global import get_current_time, RESULTS
from django.core import serializers

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

def index(request):
    return render(request, 'qa_dashboard/tcm.html', locals())

def create_catalog_page(request):
    categories = [k for k in CATALOG_CATEGORIES]
    return render(request, 'qa_dashboard/create_catalog.html', locals())


@atomic
def _create_catalog_test_case(issues):
    tcs = []
    for issue in issues:
        issue_id = int(issue.key.strip(TCMS_PROJECT).strip("-"))
        tc = None
        try:
            tc = CatalogTestCase.objects.get(jira_id=issue_id)
        except ObjectDoesNotExist:
            tc = CatalogTestCase(jira_id=issue_id)
            tc.save()
        if tc:
            tcs.append(tc)
    pks = [x.pk for x in tcs]
    return pks

def view_catalog_page(request, catalog_name):
    return render(request, 'qa_dashboard/catalog.html', locals())

def view_catalogs(request):
    return render(request, 'qa_dashboard/catalogs.html', locals())

def catalog_categories(request):
    return HttpResponse(json.dumps([k for k in CATALOG_CATEGORIES]))

def remove_catalog(request, catalog_name):
    result = initialize_result(failed=True)
    try:
        CatalogSuite.objects.get(name=catalog_name).delete()
        result["status"] = True
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))

@csrf_exempt
def execute_catalog(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    catalog_name = request_json["name"]
    owner_email = request_json["owner_email"]
    instance_name = request_json["instance_name"]

    suite_execution = add_suite_execution(submitted_time=get_current_time(),
                                          scheduled_time=get_current_time(),
                                          completed_time=get_current_time(),
                                          catalog_reference=catalog_name)

    cse = CatalogSuiteExecution(owner_email=owner_email,
                                catalog_name=catalog_name,
                                instance_name=instance_name,
                                suite_execution_id=suite_execution.execution_id)
    cse.save()

    test_cases = CatalogSuite.objects.get(name=catalog_name).test_cases.all()
    for test_case in test_cases:
        test_case_execution = add_test_case_execution(test_case_id=test_case.jira_id,
                                                      suite_execution_id=suite_execution.execution_id,
                                                      path="")
        cte = CatalogTestCaseExecution(jira_id=test_case.jira_id,
                                       execution_id=test_case_execution.execution_id,
                                       catalog_suite_execution_id=cse.suite_execution_id,
                                       engineer=Engineer.objects.get(email=owner_email),
                                       test_bed=TestBed.objects.get(name="simulation"))
        cte.save()
    result["status"] = True
    return HttpResponse(json.dumps(result))

def catalog_executions(request, catalog_name):
    return render(request, 'qa_dashboard/catalog_execution_page.html', locals())

@csrf_exempt
def catalog_suite_execution_summary(request, catalog_name):
    result = initialize_result(failed=True)
    result["status"] = True
    result["data"] = json.loads(serializers.serialize('json', CatalogSuiteExecution.objects.filter(catalog_name=catalog_name))) #TODO: Really stupid
    return HttpResponse(json.dumps(result))

def catalog_suite_execution_details(request, instance_name):
    result = initialize_result(failed=True)
    num_passed = 0
    num_failed = 0
    num_total = 0
    try:
        suite_execution = CatalogSuiteExecution.objects.get(instance_name=instance_name)
        logger.info("Retrieved suite execution id: {}".format(suite_execution.suite_execution_id))
        tex = CatalogTestCaseExecution.objects.filter(catalog_suite_execution_id=suite_execution.suite_execution_id)
        payload = {}
        payload["jira_ids"] = {}

        num_total = tex.count()

        for te in tex:
            if te.jira_id not in payload["jira_ids"]:
                payload["jira_ids"][te.jira_id] = {}
                payload["jira_ids"][te.jira_id]["instances"] = []
                # payload[te.jira_id]["summary"] = JiraManager().get_issue_attributes_by_id(id=te.jira_id)["summary"]
            instances = payload["jira_ids"][te.jira_id]["instances"]
            info = {}
            info["test_bed"] = te.test_bed
            info["execution_id"] = te.execution_id
            info["suite_execution_id"] = te.catalog_suite_execution_id
            info["owner"] = te.engineer.short_name
            info["result"] = TestCaseExecution.objects.get(execution_id=te.execution_id).result
            if info["result"] == RESULTS["PASSED"]:
                num_passed += 1
            if info["result"] == RESULTS["FAILED"]:
                num_failed += 1
            instances.append(info)
        payload["num_total"] = num_total
        payload["num_passed"] = num_passed
        payload["num_failed"] = num_failed
        result["data"] = payload
        result["status"] = True
    except ObjectDoesNotExist as ex:
        result["error_message"] = "Unable to retrieve CatalogSuiteExecution for instance {} : {}".format(instance_name,
                                                                                                         str(ex))
    except Exception as ex:
        result["error_message"] = "Unable to retrieve CatalogSuiteExecution for instance {} : {}".format(instance_name,
                                                                                                         str(ex))
    return HttpResponse(json.dumps(result))

def catalog_suite_execution_details_page(request, instance_name):
    return render(request, 'qa_dashboard/catalog_execution_details_page.html', locals())

def instance_metrics(request, instance_name):
    result = initialize_result(failed=True)
    try:
        result["status"] = True
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))

@csrf_exempt
def basic_issue_attributes(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    logger.info("basic_issue_attributes: " + str(request_json))
    jira_ids = request_json
    try:
        issue_attributes = JiraManager().get_basic_issue_attributes_by_ids(ids=jira_ids)
        result["data"] = issue_attributes
        result["status"] = True
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))

def catalogs_summary(request):
    result = initialize_result(failed=True)
    result["data"] = None
    result["status"] = True
    catalog_summary = {}
    categories = [k for k in CATALOG_CATEGORIES]
    for category in categories:
        catalog_summary[category] = {}
        catalog_summary[category]["catalogs"] = []
        matching_suites = CatalogSuite.objects.filter(category=str(category))
        for matching_suite in matching_suites:
            test_cases = matching_suite.test_cases
            test_case_count = test_cases.count()
            catalog_info = {"name": matching_suite.name,
                            "tc_count": test_case_count,
                            "execution_count": CatalogSuiteExecution.objects.filter(catalog_name=matching_suite.name).count()}
            catalog_summary[category]["catalogs"].append(catalog_info)
    result["data"] = catalog_summary
    return HttpResponse(json.dumps(result))

@csrf_exempt
def update_catalog(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    logger.info("Updating catalog: " + str(request_json))
    name = request_json["name"]
    jqls = request_json["jqls"]

    flat_jql = " ".join(jqls)

    try:
        jira_manager = JiraManager()
        issues = jira_manager.get_issues_by_jql(jql=flat_jql)
        logger.info("Issues: " + str(issues))
        if issues:
            pks = _create_catalog_test_case(issues)
            test_cases = CatalogTestCase.objects.filter(pk__in=pks)
            suite = CatalogSuite.objects.get(name=name)
            suite.jqls = json.dumps(jqls)
            suite.save()
            suite.test_cases.clear()
            suite.save()
            for test_case in test_cases:
                suite.test_cases.add(test_case.pk)
            suite.save()
    except Exception as ex:
        result["error_message"] = "JQL:" + flat_jql + "\n" + str(ex)
    return HttpResponse(json.dumps(result))


@csrf_exempt
def preview_catalog(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    jqls = request_json["jqls"]
    flat_jql = ""
    try:
        jira_manager = JiraManager()
        flat_jql = " ".join(jqls)
        issues = jira_manager.get_issues_by_jql(jql=flat_jql)
        logger.info("Issues: " + str(issues))
        payload = {}
        payload["test_cases"] = []
        for issue in issues:
            issue_attributes = jira_manager.get_issue_attributes_by_issue(issue=issue)
            payload["test_cases"].append({"jira_id": issue_attributes["id"],
                                          "summary": issue_attributes["summary"],
                                          "components": issue_attributes["components"]})

        result["data"] = payload
        result["status"] = True
    except Exception as ex:
        result["error_message"] = "JQL:" + flat_jql + "\n" + str(ex)
    return HttpResponse(json.dumps(result))

def catalog(request, catalog_name):
    result = initialize_result(failed=True)
    suite = CatalogSuite.objects.get(name=catalog_name)
    payload = {}
    payload["name"] = suite.name
    payload["category"] = suite.category
    payload["test_cases"] = []
    payload["jqls"] = json.loads(suite.jqls)
    jira_manager = JiraManager()

    try:
        for test_case in suite.test_cases.all():
            issue_attributes = jira_manager.get_issue_attributes_by_id(id=test_case.jira_id)
            payload["test_cases"].append({"jira_id": test_case.jira_id,
                                          "summary": issue_attributes["summary"],
                                          "components": issue_attributes["components"]})
    except Exception as ex:
        result["error_message"] = str(ex)
    result["status"] = True
    result["data"] = payload
    return HttpResponse(json.dumps(result))

@csrf_exempt
def create_catalog(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    logger.info("Catalog info: " + str(request_json))
    try:
        jira_manager = JiraManager()
        issues = jira_manager.get_issues_by_jql(jql=request_json["jql"])
        logger.info("Issues: " + str(issues))
        jql = request_json["jql"]
        if issues:
            pks =_create_catalog_test_case(issues)
            test_cases = CatalogTestCase.objects.filter(pk__in=pks)
            suite = CatalogSuite(name=request_json["name"],
                                 category=request_json["category"],
                                 jqls=json.dumps([jql]))
            suite.save()
            for test_case in test_cases:
                suite.test_cases.add(test_case.pk)
            suite.save()
        result["status"] = True
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))