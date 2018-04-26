from lib.system.fun_test import fun_test
import glob
import os
import sys


all_classses = []
directories = ["storage", "networking", "security"]
base_path = "/Users/johnabraham/PycharmProjects/fun_test/Integration/fun_test/scripts"
for directory in directories:
    sys.path.append(base_path + "/" + directory)
    files = glob.glob(pathname=base_path + "/" + directory + "/*.py")
    for file in files:
        classes = fun_test.inspect(module_name=file)
        for klass in classes['classes']:
            s = "{}\t{}\t{}".format(directory, os.path.basename(file), klass["summary"])
            all_classses.append(s)


for k in all_classses:
    print k