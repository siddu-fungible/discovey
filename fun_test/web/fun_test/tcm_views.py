from fun_settings import TCMS_PROJECT
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.shortcuts import render
import logging, json
from web.fun_test.tcm_common import CATALOG_CATEGORIES
from web_global import initialize_result
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.jira_manager import JiraManager
from web.fun_test.jira_models import CatalogSuite, CatalogTestCase
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic
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

def view_catalog_page(request):
    return render(request, 'qa_dashboard/catalog.html', locals())

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

def catalog(request):
    result = initialize_result(failed=True)
    suite = CatalogSuite.objects.get(name="catalog-1")
    payload = {}
    payload["name"] = suite.name
    payload["category"] = suite.category
    payload["test_cases"] = []
    payload["jqls"] = json.loads(suite.jqls)
    try:
        for test_case in suite.test_cases.all():
            jira_manager = JiraManager()
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

    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))