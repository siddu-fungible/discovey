from lib.system.fun_test import fun_test
from fun_settings import *

from fun_global import *
from jira import JIRA
import jira
import os, traceback

class JiraManager:
    def __init__(self, project_name=TCMS_PROJECT):
        self.project_name = project_name
        if "JIRA_PASS" in os.environ:
            password = os.environ["JIRA_PASS"]
        self.jira = JIRA(JIRA_URL, basic_auth=("automation", "Precious1*"))
        fun_test.debug("JIRA Manager initialization complete")

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
            fun_test.critical("Exception: {}".format(str(ex)))
        return result

    def get_issues(self, component=None):
        result = None
        if component:
            result = self.jira.search_issues(jql_str="component={}".format(component))
        return result

    def get_project(self):
        project = None
        try:
            project = self.jira.project(self.project_name)
        except Exception as ex:
            fun_test.critical(str(ex))
        return project

    def get_project_components(self):
        components = []
        project = self.get_project()
        if project:
            components = self.jira.project_components(project=self.project_name)
        return components

if __name__ == "__main__":
    from lib.system.fun_test import FunTimer
    m = JiraManager()

    print m.get_issues(component="nw-bgp")
    print m.get_project_components()
    # ft = FunTimer(max_time=1)
    # m.update_test_case(id=27, summary="Some summary", description="Some description")
    #print m.is_issue_present(id=2)
    #m.generate_issue()
    #print ft.elapsed_time()