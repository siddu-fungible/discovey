from fun_settings import *
from jira import JIRA


def update_test_case(id, summary, summary):
    jira = JIRA(JIRA_URL, basic_auth=("john.abraham", "Loopking1234$"))
    issue_id = '{}-{}'.format(TCMS_PROJECT, id)
    issue = jira.issue(issue_id)
    issue.update(summary=summary, summary=summary)


if __name__ == "__main__":
    update_test_case(id=1, summary="Some summary", summary="Some summary")