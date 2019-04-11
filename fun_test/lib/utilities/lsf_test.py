from lib.host.lsf_status_server import LsfStatusServer
import re
import json
import collections

lsf_server = LsfStatusServer()

lsf_results = collections.OrderedDict()
prefix = "qa_triage_bcopy_"
for i in range(0, 16):
    jobs = lsf_server.get_past_jobs_by_tag(tag="qa_triage_bcopy_{}".format(i), add_info_to_db=False)
    if jobs:

        for job in jobs:
            job_id = job["job_id"]
            j = lsf_server.get_job_by_id(job_id=job_id)
            j = json.loads(j)
            lsf_results[j["job_dict"]["branch_funos"]] = j["output_text"]


print "parse results"
for git_commit, output_text in lsf_results.iteritems():
    #m = re.search(r'coherent', lsf_result, re.MULTILINE)

    # print lsf_result
    lines = output_text.split("\n")
    for line in lines:
        m = re.search(r'bcopy \(coherent, dma\) 4KB 20 times; average bandwidth:', line, re.MULTILINE|re.DOTALL)
        if m:

            m2 = re.search(r'{\s+"value":\s+(\S+),.*}', line)
            if m2:
                print git_commit, m2.group(1)
