from fun_settings import *
from django.core.management import execute_from_command_line
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir)

if __name__ == "__main__":
    execute_from_command_line(["", "runserver", "0.0.0.0:%d" % WEB_SERVER_PORT])
