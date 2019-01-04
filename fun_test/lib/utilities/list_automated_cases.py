from __future__ import absolute_import
from lib.system.fun_test import fun_test
import glob
import os
import sys


all_classses = []
# directories = ["storage", "networking", "security"]
# directories = ["storage", "security"]
directories = ["storage"]

file_based_view = {}

base_path = "/Users/johnabraham/PycharmProjects/fun_test/Integration/fun_test/scripts"
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
                file_based_view.setdefault(os.path.basename(file), []).append(klass["summary"])

# for k in all_classses:
# print k

f = open("automated_cases.txt", "w")

for k, v in file_based_view.iteritems():
    print "Script: {}\n".format(k)
    f.write("{},\n".format(k))
    for test_case in v:
        print test_case
        f.write("," + test_case + "\n")
