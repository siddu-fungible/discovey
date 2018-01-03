#!/usr/bin/env python
from fun_settings import *
from django.core.management import execute_from_command_line
import os, sys, psutil, subprocess, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir)
os.environ["REGRESSION_SERVER"] = "1"

rq_found = False
redis_found = False
for proc in psutil.process_iter():
    try:
        cmd_line = proc.cmdline()
        for s1 in cmd_line:
            if "redis" in s1:
                print("Redis found")
                redis_found = True
            if "worker" in s1 and (proc.name() == "rq"):
                print("Rq found")
                rq_found = True
    except:
        pass

if not rq_found:
    print("Rq not found: Start it with \"rq worker\" on a separate shell or nohup")
    sys.exit(-1)

if not redis_found:
    print("Redis not found: Start it with \"redis-server\"")
    sys.exit(-1)


if __name__ == "__main__":
    # execute_from_command_line(["", "run_scheduler"])
    execute_from_command_line(["", "runserver", "0.0.0.0:%d" % WEB_SERVER_PORT])
