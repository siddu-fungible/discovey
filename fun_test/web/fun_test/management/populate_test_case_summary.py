from fun_settings import SCRIPTS_DIR
from web.fun_test.django_interactive import *
from web.fun_test.models import TestCaseInfo
from lib.system.fun_test import fun_test
import sys
import glob

test_case_infos = TestCaseInfo.objects.all()

for test_case_info in test_case_infos:
    print test_case_info

base_path = SCRIPTS_DIR
#directories = ["storage", "networking", "security"]
directories = ["storage", "accelerators", "examples", "networking", "security", "system"]
directories = ["storage"]
file_based_view = {}

all_classses = []
import fnmatch
import os

matches = []
for root, dirnames, filenames in os.walk(SCRIPTS_DIR):
    for filename in fnmatch.filter(filenames, '*.py'):
        absolute_path = os.path.join(root, filename)
        if "scratch" in absolute_path or "examples" in absolute_path:
            continue
        # matches.append(os.path.join(root, filename))
        try:
            print absolute_path
            classes = fun_test.inspect(module_name=absolute_path)
            for klass in classes['classes']:
                if klass["summary"]:
                    # s = "{}\t{}\t{}".format(directory, os.path.basename(file), klass["summary"])
                    # all_classses.append(s)
                    # file_based_view[os.path.basename(file)].append(klass["summary"])
                    record = {"id": klass["id"], "summary": klass["summary"]}
                    file_name = absolute_path.replace(SCRIPTS_DIR, "")
                    if file_name not in file_based_view:
                        file_based_view[file_name] = []
                    file_based_view[file_name].append(record)

        except Exception as ex:
            pass
"""
for directory in directories:
    sys.path.append(base_path + "/" + directory)
    files = glob.glob(pathname=base_path + "/" + directory + "/*.py")
    for file in files:
        classes = fun_test.inspect(module_name=file)
        for klass in classes['classes']:
            if klass["summary"]:
                s = "{}\t{}\t{}".format(directory, os.path.basename(file), klass["summary"])
                all_classses.append(s)
                # file_based_view[os.path.basename(file)].append(klass["summary"])
                file_based_view.setdefault(file.replace(SCRIPTS_DIR, ""), []).append(klass["summary"])
"""

tcs = TestCaseInfo.objects.filter(script_path="/networking/funeth/pcie_host.py")

for tc in tcs:
    print tc


for k, v in file_based_view.iteritems():
    print "Script: {}\n".format(k)
    for test_case_index, test_case in enumerate(v):
        print test_case_index, ":", test_case["id"], ":", test_case["summary"]
        try:
            TestCaseInfo.add_update(test_case_id=test_case["id"], summary=test_case["summary"], script_path=k)
        except:
            pass
    print
