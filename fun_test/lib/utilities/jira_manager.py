from fun_settings import *
from fun_global import *
from jira import JIRA
import jira
import os, traceback

class JiraManager:
    def __init__(self):
        password = "TPS-1"
        if "JIRA_PASS" in os.environ:
            password = os.environ["JIRA_PASS"]
        self.jira = JIRA(JIRA_URL, basic_auth=("john.abraham", password))

    def get_issue_id(self, id):
        return '{}-{}'.format(TCMS_PROJECT, id)

    def generate_issue(self):
        result = {"status": RESULT_FAIL, "err_msg": "Not run", "issue": None, "issue_id": None}
        try:
            new_issue = self.jira.create_issue(project=TCMS_PROJECT,
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
        issue_id = '{}-{}'.format(TCMS_PROJECT, id)
        issue = jira.issue(issue_id)
        issue.update(summary=summary, description=description)

    def is_issue_present(self, id):
        result = None
        issue_id = self.get_issue_id(id=id)
        jql = "project={} and id={}".format(TCMS_PROJECT, issue_id)
        try:
            issues_list = self.jira.search_issues(jql_str=jql)
            result = (len(issues_list) == 1)
        except jira.exceptions.JIRAError as ex:
            if not 'does not exist' in ex.text:
                raise ex
        except Exception as ex:
            print("Exception: {}".format(str(ex)))
        return result

if __name__ == "__main__":
    from lib.system.fun_test import FunTimer
    m = JiraManager()
    ft = FunTimer(max_time=1)
    m.update_test_case(id=27, summary="Some summary", description="Some description")
    #print m.is_issue_present(id=2)
    #m.generate_issue()
    #print ft.elapsed_time()