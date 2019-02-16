#!/usr/bin/env python
from django.core.management import execute_from_command_line
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
os.environ["DEVELOPMENT_MODE"] = "1"
from fun_settings import *

if __name__ == "__main__":
    execute_from_command_line(["", "runserver", "0.0.0.0:%d" % WEB_SERVER_PORT])
