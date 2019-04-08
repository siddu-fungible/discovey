from django.core.management.base import BaseCommand
import time, subprocess, os, signal
from fun_settings import SCHEDULER_DIR ,SCHEDULER_PID

class Command(BaseCommand):

    def handle(self, *args, **options):
        return self.launch_scheduler()

    def launch_scheduler(self):
        print("Launching Scheduler")
        if os.path.exists(SCHEDULER_PID):
            try:
                with open(SCHEDULER_PID, "r") as f:
                    scheduler_pid = f.read()
                    signals = [signal.SIGTERM, signal.SIGKILL]
                    print("Killing old scheduler")
                    for sig in signals:
                        try:
                            os.kill(int(scheduler_pid), sig)
                            time.sleep(5)
                        except Exception as ex:
                            print("launch_scheduler: " + str(ex))
                    os.remove(SCHEDULER_PID)
                    print("Killed old scheduler")
            except Exception as ex:
                print("Run_scheduler:" + str(ex))
        p = subprocess.Popen(["./scheduler.py"], cwd=SCHEDULER_DIR, env=os.environ.copy())  # TODO Validate this
        time.sleep(5)



