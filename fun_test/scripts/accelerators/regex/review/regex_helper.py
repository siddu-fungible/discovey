from lib.system.fun_test import *
import os, re


def validate_rgx_result(data_store_dir, job_dir, num_polls=10, private_run=True):
    print "data store:", data_store_dir
    test_result = True
    remote_fuons_logs_file = job_dir + "/mail.txt"
    if private_run:
        for poll in range(num_polls):
            local_funos_logs_file = data_store_dir + "/" + job_dir.split("/")[-1] + ".txt"
            fun_test.scp(source_file_path=remote_fuons_logs_file,
                         source_ip="qa-ubuntu-02",
                         source_username="auto_admin",
                         source_password="fun123",
                         source_port=22,
                         target_file_path=local_funos_logs_file,
                         recursive=False,
                         timeout=300)
            if os.path.exists(local_funos_logs_file):
                fun_test.log("SCP of mail.txt successful")
                break
            else:
                fun_test.sleep("Polling for mail.txt...",60)
        with open(local_funos_logs_file, "r") as f_in:
            log_data = f_in.read()
    else:
        for poll in range(num_polls):
            if os.path.exists(remote_fuons_logs_file):
                fun_test.log(remote_fuons_logs_file+" available")
                break
            else:
                fun_test.sleep("Polling for "+ remote_fuons_logs_file+ "...", 3*60)
        with open(remote_fuons_logs_file, "r") as f_in:
            log_data = f_in.read()

    try:
        action_seq = re.findall('(?:ACTION SEQUENCE\s.*)', log_data)
        fun_test.test_assert(len(action_seq) != 0, "Action sequence found in FunOS logs")
        for action in action_seq:
            all_bad_searches = re.findall("\(search\).*but.*", log_data)
            all_loads = re.findall("\(load\).*:.*", log_data)
            all_unloads = re.findall("\(unload\).*:.*", log_data)

            try:
                fun_test.test_assert(len(all_loads) > 0, "LOADS: " + ", ".join(all_loads))
            except:
                pass

            try:
                fun_test.test_assert(len(all_bad_searches) == 0, "BAD SEARCHES: " + ", ".join(all_bad_searches))
            except:
                pass

            try:
                fun_test.test_assert(len(all_unloads) > 0, "UNLOADS: " + ", ".join(all_unloads))
            except:
                pass

            action_id = re.search("ACTION SEQUENCE (\d+)", action).group(1)
            pass_num = re.search("PASS (\d+)", action).group(1)
            fail_num = re.search("FAIL (\d+)", action).group(1)
            mismatch_num = re.search("MISMATCHES (\d+)", action).group(1)

            try:
                fun_test.test_assert(int(pass_num) > 0,
                                     "Sequence: {}; Pass number: {}".format(action_id, pass_num))
            except:
                pass
            try:
                fun_test.test_assert(int(fail_num) == 0,
                                     "Sequence: {}; Fail number: {}".format(action_id, fail_num))
            except:
                test_result = False
                pass
            try:
                fun_test.test_assert(int(mismatch_num) == 0,
                                     "Sequence: {}; Mismatch number: {}".format(action_id, mismatch_num))
            except:
                test_result = False
                pass
    except:
        test_result = False
        try:
            fun_test.test_assert(test_result, "found ACTION_SEQUENCE or PASS/FAIL/MISMATCHES in log data")
        except:
            pass

    if not test_result:
        return False

    return True

def validate_job(lsf_status_server,tag=""):
    job_resp = lsf_status_server.get_jobs_by_tag(tag)
    job_info = json.loads(job_resp)
    if job_info["past_jobs"] != []:
        job_dir = job_info['past_jobs'][0]['job_dir']
    else:
        job_dir = job_info['running_jobs'][0]['job_dir']
    fun_test.log("job directory:" + job_dir)
    return job_dir