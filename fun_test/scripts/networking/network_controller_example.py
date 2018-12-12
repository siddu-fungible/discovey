from lib.host.network_controller import *
from lib.system.fun_test import *

class MyScript(FunTestScript):
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


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity Test 1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)
        job_environment = fun_test.get_job_environment()
        fun_test.test_assert(job_environment, "Job environment provided")
        fun_test.print_key_value(title=None, data=job_environment)
        dpc_proxy_ip = job_environment['UART_HOST']
        dpc_proxy_port = job_environment['UART_TCP_PORT_0']
        try:
            fun_test.log("Connecting to Remote DPC %s on port %d" % (dpc_proxy_ip, dpc_proxy_port))
            network_controller_obj = NetworkController(dpc_server_ip=dpc_proxy_ip, dpc_server_port=dpc_proxy_port,
                                               verbose=True)

            psw_stats = network_controller_obj.peek_psw_global_stats()
            print psw_stats

            network_controller_obj.echo_hello()

        except Exception as ex:
            print ex

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.log("Running Dummy test")
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
