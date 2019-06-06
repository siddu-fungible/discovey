#!/usr/bin/env python
from django.core.management import execute_from_command_line
import os
os.environ["DISABLE_FUN_TEST"] = "1"
import argparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
os.environ["PRODUCTION_MODE"] = "1"
from fun_settings import *

WEB_SERVER_PID_LOCATION = "/tmp/fun_test_web_server.pid"

def write_pid():
    with open(WEB_SERVER_PID_LOCATION, "w") as fp:
        fp.write(str(os.getpid()))

def get_old_pid():
    old_pid = None
    if os.path.exists(WEB_SERVER_PID_LOCATION):
        with open(WEB_SERVER_PID_LOCATION, "r") as fp:
            old_pid = fp.read().strip()
    return old_pid

def kill_old_process():
    old_pid = get_old_pid()
    if old_pid:
        print "Old PID: {}".format(old_pid)
        try:
            os.kill(int(old_pid), 9)
        except:
            pass
        os.remove(WEB_SERVER_PID_LOCATION)

def initialize():
    kill_old_process()
    write_pid()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Django production mode")
    parser.add_argument('--under_construction',
                        dest="under_construction",
                        default=None,
                        help="Enable the site to be under construction")
    args = parser.parse_args()
    site_under_construction = args.under_construction
    del os.environ["DISABLE_FUN_TEST"]
    if site_under_construction:
        os.environ["SITE_UNDER_CONSTRUCTION"] = "1"
    else:
        if "SITE_UNDER_CONSTRUCTION" in os.environ:
            del os.environ["SITE_UNDER_CONSTRUCTION"]

    initialize()
    execute_from_command_line(["", "runserver", "--noreload", "0.0.0.0:%d" % WEB_SERVER_PORT])
