from fun_settings import *
from django.core.management import execute_from_command_line
import os, sys
from threading import Thread

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir)

enable_celery = False

class CeleryThread(Thread):
    def run(self):
        from celery.__main__ import main
        sys.argv.append("worker")
        sys.argv.append("-A")
        sys.argv.append("tools")
        main()


if __name__ == "__main__":
    if enable_celery:
        celery_thread_obj = CeleryThread()
        celery_thread_obj.start()
    execute_from_command_line(["", "runserver", "0.0.0.0:%d" % WEB_SERVER_PORT])
    if enable_celery:
        celery_thread_obj.join()