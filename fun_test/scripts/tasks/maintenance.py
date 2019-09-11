from lib.system.fun_test import *
from lib.templates.tasks.tasks_template import TaskTemplate

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
        t = TaskTemplate()
        t.call("sudo kill -9 $(ps -eo comm,pid,etimes,cmd | awk '/^ssh/ {if ($3 > 36000) { print $2 }}')")






if __name__ == "__main__":
    myscript = MaintenanceScript()
    myscript.add_test_case(ManageSsh())
    myscript.run()
