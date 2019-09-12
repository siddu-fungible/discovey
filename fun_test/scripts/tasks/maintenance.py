from lib.system.fun_test import *
from lib.templates.tasks.tasks_template import TaskTemplate
import subprocess

class MaintenanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")

class ManageSsh(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Manage SSH connections",
                              steps="""
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        max_allowed_ssh = 1024
        t = TaskTemplate()
        t.call("sudo kill -9 $(ps -eo comm,pid,etimes,cmd | awk '/^ssh/ {if ($3 > 36000) { print $2 }}')")
        commands = ["ps -ef", "grep ssh", "wc -l"]
        t.piped_commands(commands=commands)
        # active_ssh = t.popen("ps", ["-ef", "\|",  "grep", "ssh", "\|", "wc", "-l"])
        return_code, output, err = t.piped_commands(commands=["ps -ef", "grep ssh"])
        fun_test.simple_assert(not return_code, "Return code valid")
        all_sshs = output.split("\n")
        for ssh in all_sshs:
            fun_test.log(ssh)
        fun_test.test_assert(len(all_sshs) <= max_allowed_ssh, "Num ssh < {}".format(max_allowed_ssh))


if __name__ == "__main__":
    myscript = MaintenanceScript()
    myscript.add_test_case(ManageSsh())
    myscript.run()
