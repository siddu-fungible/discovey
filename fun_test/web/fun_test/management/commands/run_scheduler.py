from django.core.management.base import BaseCommand
import time, subprocess
from fun_settings import SCHEDULER_DIR

class Command(BaseCommand):

    def handle(self, *args, **options):
        return self.launch_scheduler()

    def launch_scheduler(self):
        print("Launching Scheduler")
        p = subprocess.Popen(["./scheduler.py"], cwd=SCHEDULER_DIR)  # TODO Validate this
        time.sleep(5)
        result = p.poll()



