from __future__ import absolute_import
import os
os.environ["DISABLE_FUN_TEST"] = "1"
from lib.system.fun_test import fun_test
import glob
import sys


def a():
    all_classses = []
    directories = ["storage", "networking", "security"]
    # directories = ["storage", "security"]
    directories = ["storage"]
    directories = ["networking"]

    #def list_cases(directories, )
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
            # fun_test.critical("Unable to parse: {}".format(file))
    # for k in all_classses:
    # print k

    f = open("automated_cases.txt", "w")

    for k, v in file_based_view.iteritems():
        print "Script: {}\n".format(k)
        f.write("{},\n".format(k))
        for test_case in v:
            print test_case
            f.write("," + test_case + "\n")

if __name__ == "__main__":
    print fun_test.inspect(sys.argv[1])
