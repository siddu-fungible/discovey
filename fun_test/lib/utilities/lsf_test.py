from lib.host.lsf_status_server import LsfStatusServer
from lib.utilities.git_utilities import GitManager
import re
import json
import collections

base_tag = "qa_triage_malloc_agent"
iteration = 1
lsf_server = LsfStatusServer()
num_commits = 64
num_sections = 4
step = num_commits/num_sections
if not step:
    step = 1
lsf_results = collections.OrderedDict()
prefix = "{}_{}".format(base_tag, iteration)
for i in range(0, num_commits, step):
    this_tag = "{}_{}".format(prefix, i)
    print "This-tag: {}".format(this_tag)
    jobs = lsf_server.get_past_jobs_by_tag(tag=this_tag, add_info_to_db=False)
    if jobs:

        for job in jobs:
            job_id = job["job_id"]
            j = lsf_server.get_job_by_id(job_id=job_id)
            j = json.loads(j)
            lsf_results[j["job_dict"]["branch_funos"]] = {"output_text": j["output_text"], "tag": this_tag}


print "parse results"
for git_commit, value in lsf_results.iteritems():
    #m = re.search(r'coherent', lsf_result, re.MULTILINE)

    # print lsf_result

    output_text = value["output_text"]
    tag = value["tag"]
    lines = output_text.split("\n")
    for line in lines:
        m = re.search('fun_magent_rate_malloc_free_per_sec', line, re.MULTILINE|re.DOTALL)
        if m:

            c = GitManager().get_commit(sha=git_commit)
            d = c["commit"]["committer"]["date"]
            print git_commit, tag, line, d, m.group(0)

