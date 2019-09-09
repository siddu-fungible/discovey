from web.fun_test.django_interactive import *
from lib.system.fun_test import *
from web.fun_test.metrics_lib import *

ml = MetricLib()


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")



class MonitorDockerProcesses(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Monitor docker processes",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def cleanup(self):
        pass

    def setup(self):
        pass

    def run(self):
        os.system("docker ps -a")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(MonitorDockerProcesses())
    myscript.run()
