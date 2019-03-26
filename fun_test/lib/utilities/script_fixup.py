from fun_settings import *
from fun_global import *
import traceback, os
from lib.utilities.jira_manager import JiraManager



def fix(script_path, id):
    result = {"status": RESULT_FAIL, "err_msg": "Not run"}
    try:
        f = open(script_path, "r")
        content = f.read()
        f.close()
        f = open(script_path, "w")
        content = content.replace("$tc", "{}".format(id), 1)
        f.write(content)
        f.close()


        result["status"] = RESULT_PASS
        result["err_msg"] = ""
    except Exception as ex:
        result["err_msg"] = "{}\n{}".format(traceback.format_exc(), str(ex))
    return result

if __name__ == "__main__":
    # print fix(script_path="lllala")
    issue_id = "14"
    fix(script_path='/Users/johnabraham/PycharmProjects/test2/Integration/fun_test/scripts/examples/sanity_tc.py', id=issue_id)
