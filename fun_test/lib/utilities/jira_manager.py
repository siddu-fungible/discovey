from fun_settings import *
import logging
from fun_global import *
from jira import JIRA
import jira
import os, traceback

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
if not logger.handlers:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(hdlr=handler)
    logger.setLevel(logging.DEBUG)

class JiraManager:
    def __init__(self, project_name=TCMS_PROJECT):
        self.project_name = project_name
        if "JIRA_PASS" in os.environ:
            password = os.environ["JIRA_PASS"]
        self.jira = JIRA(JIRA_URL, basic_auth=("automation", "Precious1*"), timeout=20)
        logger.debug("JIRA Manager initialization complete")

    def get_issue_id(self, id):
        return '{}-{}'.format(self.project_name, id)

    def generate_issue(self):
        result = {"status": RESULT_FAIL, "err_msg": "Not run", "issue": None, "issue_id": None}
        try:
            new_issue = self.jira.create_issue(project=self.project_name,
                                               summary='Generated Issue',
                                               description='', issuetype={'name': 'Test-case'})
            result["status"] = RESULT_PASS
            result["issue"] = new_issue
            result["issue_id"] = new_issue.key.replace(TCMS_PROJECT + "-", "")
        except Exception as ex:
            result["err_msg"] = "{}\n{}".format(traceback.format_exc(), str(ex))
        return result

    def update_test_case(self, id, summary, description):
        jira = self.jira
        issue_id = self.get_issue_id(id=id)
        issue = jira.issue(issue_id)
        issue.update(summary=summary, description=description)

    def is_issue_present(self, id):
        result = None
        issue_id = self.get_issue_id(id=id)
        jql = "project={} and id={}".format(self.project_name, issue_id)
        try:
            issues_list = self.jira.search_issues(jql_str=jql)
            result = (len(issues_list) == 1)
        except jira.exceptions.JIRAError as ex:
            if not 'does not exist' in ex.text:
                raise ex
        except Exception as ex:
            logger.exception("Exception: {}".format(str(ex)))
        return result

    def get_issue_by_id(self, id):
        result = None
        issue_id = self.get_issue_id(id=id)
        jql = "project={} and id={}".format(self.project_name, issue_id)
        try:
            issues_list = self.jira.search_issues(jql_str=jql)
            if issues_list:
                result = issues_list[0]
        except jira.exceptions.JIRAError as ex:
            if not 'does not exist' in ex.text:
                raise ex
        except Exception as ex:
            logger.exception("Exception: {}".format(str(ex)))
        return result

    def get_issue_attributes_by_id(self, id):
        issue = self.get_issue_by_id(id=id)
        attributes = {}
        if issue:
            attributes = self.get_issue_attributes_by_issue(issue=issue)
        return attributes

    def get_issue_attributes_by_issue(self, issue):
        attributes = {}
        attributes["summary"] = issue.fields.summary
        attributes["components"] = [str(x) for x in issue.fields.components]
        attributes["id"] = int(issue.key.replace(self.project_name + "-", ""))
        attributes["module"] = getattr(issue.fields, self._get_custom_field_string("module")).value
        return attributes

    def get_issues(self, component=None):
        return self.get_issues_by_jql("component={}".format(component))

    def get_issues_by_jql(self, jql):
        logger.info("JQL: {}".format(jql))
        result = self.jira.search_issues(jql_str=jql)
        return result

    def get_project(self):
        project = None
        try:
            project = self.jira.project(self.project_name)
        except Exception as ex:
            logger.exception(str(ex))
        return project

    def get_project_components(self):
        components = []
        project = self.get_project()
        if project:
            components = self.jira.project_components(project=self.project_name)
        return components

    def _get_jql_for_ids(self, ids):
        s = ""
        if len(ids):
            s = "id={}-{}".format(self.project_name, ids[0])
            for id in ids[1:]:
                s += " or id={}-{}".format(self.project_name, id)
        return s

    def get_basic_issue_attributes_by_ids(self, ids):
        jql = self._get_jql_for_ids(ids=ids)
        issues = self.get_issues_by_jql(jql)
        issue_attributes = {}
        for issue in issues:
            attributes = self.get_issue_attributes_by_issue(issue)
            issue_attributes[attributes["id"]] = attributes
        return issue_attributes

    def create_test_case(self,
                         summary,
                         description,
                         module,
                         setup,
                         variations,
                         components,
                         test_type,
                         priority,
                         expected_result,
                         automatable=None,
                         test_bed=None):
        issue_id = None
        components = [{"name": x} for x in components]
        try:
            project = self.get_project()
            issue_dict = {
                "project": project.id,
                "summary": summary,
                "description": description,
                "issuetype": "Test-case",
                "components": components,
                "priority": {"name": priority},
                self._get_custom_field_string("module"): {"value": module},
                self._get_custom_field_string("setup"): setup,
                self._get_custom_field_string("variations"): variations,
                self._get_custom_field_string("expected_result"): expected_result,
                self._get_custom_field_string("test_type"): {"value": test_type},
                # self._get_custom_field_string("test_bed"): [{"value": test_bed}],  #TODO
                self._get_custom_field_string("automatable"): {"value": automatable}
            }
            issue = self.jira.create_issue(fields=issue_dict)
            issue_id = issue.key.replace(TCMS_PROJECT + "-", "")
            logger.debug("Issue: {} created".format(issue_id))
        except Exception as ex:
            logger.critical(str(ex))
        return issue_id

    def update_test_case_with_fields(self,
                                     id,
                                     summary,
                                     description,
                                     module,
                                     setup,
                                     variations,
                                     components,
                                     test_type,
                                     priority,
                                     expected_result,
                                     automatable=None,
                                     test_bed=None):
        jira = self.jira
        issue_id = self.get_issue_id(id=id)
        issue = jira.issue(issue_id)
        components = [{"name": x} for x in components]
        try:
            project = self.get_project()
            issue_dict = {
                "summary": summary,
                "description": description,
                "components": components,
                "priority": {"name": priority},
                self._get_custom_field_string("module"): {"value": module},
                self._get_custom_field_string("setup"): setup,
                self._get_custom_field_string("variations"): variations,
                self._get_custom_field_string("expected_result"): expected_result,
                self._get_custom_field_string("test_type"): {"value": test_type},
                # self._get_custom_field_string("test_bed"): [{"value": test_bed}],  #TODO
                self._get_custom_field_string("automatable"): {"value": automatable}
            }
            issue.update(fields=issue_dict)
            logger.debug("Issue: {} updated".format(issue_id))
        except Exception as ex:
            logger.critical(str(ex))
        return issue_id

    def _get_custom_field_string(self, field_name):
        custom_field_mapping = {
            "setup": "customfield_10305",
            "module": "customfield_10301",
            "variations": "customfield_10307",
            "test_type": "customfield_10304",
            "test_bed": "customfield_10302",
            "expected_result": "customfield_10306",
            "automatable": "customfield_10308"

        }
        return custom_field_mapping[field_name]

    def summary_exists(self, summary, module, components):
        component_str = "component in (" + ",".join(components) + ")"
        module_str = "module = {}".format(module)
        result = False
        jql = "summary ~ \"{}\" and {} and {}".format(summary, component_str, module_str)
        try:
            issues = self.get_issues_by_jql(jql=jql)
            if issues:
                result = self.get_issue_attributes_by_issue(issues[0])["id"]
        except jira.exceptions.JIRAError as ex:
            logger.debug("JIRA summary {} does not exist".format(summary))
        except Exception as ex:
            logger.critical("Fix this: {}".format(str(ex)))
        return result

if __name__ == "__main__":
    from lib.system.fun_test import FunTimer
    m = JiraManager()
    '''
    print m.create_test_case(summary="Summary 1",
                             description="Description 1",
                             module="networking",
                             setup="Setup 1",
                             variations="Variations1",
                             components=["nw-bgp", "nw-isis"],
                             test_type="functional",
                             priority="High",
                             expected_result="Expected Result1",
                             automatable="yes",
                             test_bed="Simulation")
    '''
    print m.summary_exists(summary="Summary John")
    # print m.get_issues(component="nw-bgp")
    # print m.get_project_components()
    # ft = FunTimer(max_time=1)
    # m.update_test_case(id=27, summary="Some summary", description="Some description")
    #print m.is_issue_present(id=2)
    #m.generate_issue()
    #print ft.elapsed_time()