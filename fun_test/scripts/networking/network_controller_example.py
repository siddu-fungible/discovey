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
        self.job_environment = fun_test.get_job_environment()
        fun_test.test_assert(self.job_environment, "Job environment provided")
        fun_test.print_key_value(title=None, data=self.job_environment)
        self.dpc_proxy_ip = str(self.job_environment['UART_HOST'])
        self.dpc_proxy_port = int(self.job_environment['UART_TCP_PORT_0'])

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.log("Running Dummy test")
        fun_test.log("Connecting to Remote DPC %s on port %d" % (self.dpc_proxy_ip, self.dpc_proxy_port))
        network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port,
                                           verbose=True)

        #hello_output = network_controller_obj.json_execute(verb="echo", data=['frst hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #parser_stats = network_controller_obj.json_execute(verb='peek', data="stats/prsr/nu", command_duration=120)
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.log("PSW Stats: %s \n" % parser_stats)

        #hello_output = network_controller_obj.json_execute(verb="echo", data=['2nd hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #network_controller_obj.dpc_shutdown()
        network_controller_obj.disconnect()
        del network_controller_obj

        network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port,
                                           verbose=True)
        #hello_output = network_controller_obj.json_execute(verb="echo", data=['last hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #del network_controller_obj

        #fun_test.log("sleeping 2 mins...\n")
        #time.sleep(120)
        #network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port, verbose=True)

        #hello_output=str(network_controller_obj.echo_hello())
        #fun_test.log(hello_output)
        #parser_stats = network_controller_obj.peek_parser_stats()
        #fun_test.log("PSW Stats: %s \n" % parser_stats)


        #network_controller_obj.dpc_shutdown()
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
