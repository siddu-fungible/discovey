#!/usr/bin/env python
from fun_settings import *
from django.core.management import execute_from_command_line
import os, sys, psutil, subprocess, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir)

enable_rq_worker = False
if enable_rq_worker:
    rq_found = False
    for proc in psutil.process_iter():
        try:
            s = [s for s in proc.cmdline() if "rq worker" in s]
            if s:
                rq_found = True
        except:
            pass
    if not rq_found:
        subprocess.Popen(["rq worker"], shell=True, cwd=WEB_DIR)
        subprocess.Popen(["redis-server"], shell=True, cwd=WEB_DIR)



if __name__ == "__main__":
    # execute_from_command_line(["", "run_scheduler"])
    execute_from_command_line(["", "runserver", "0.0.0.0:%d" % WEB_SERVER_PORT, "--noreload"])
