# Suite ==> JQLs
# ... cache TCs
# ... Delete
# ... set topology
# ... Selected


# Tc

from django.db import models
from web.fun_test.tcm_common import CATALOG_CATEGORIES
from django.core import serializers
from jira import JIRA
import jira
import cgitb
import git
from git import Repo
from fun_settings import *
from lib.utilities.jira_manager import JiraManager
import requests

if __name__ == "__main__":
    jira = JIRA(JIRA_URL, basic_auth=("automation", "Precious1*"), timeout=20)
    projects = jira.projects()
    for project in projects:
        project = "IN"
        obj = JiraManager(project_name=project)
        id = 10
        query = 'project="IN" and id="IN-10"'
        issues = obj.get_issues_by_jql(jql=query)

        issues = jira.search_issues(jql_str=query)
        # for issue in issues:
        #     #print issue.key,issue.self
        #     if issue.fields.description and "Average wustack alloc/free cycles" in issue.fields.description:
        print "found"
    print "completed"
    # repo = requests.get("https://github.com/fungible-inc/FunOS/")
    # commits_list = list(repo.iter_commits())
    # print "git completed"
