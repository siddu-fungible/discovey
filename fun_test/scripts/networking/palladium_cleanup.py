from lib.system.fun_test import *
from lib.host.palladium import Palladium, DpcshProxy

PALLADIUM_HOST_FILE = "/palladium_hosts.json"

config = {}
palladium_boot_up_obj = None
dpcsh_proxy_obj = None


class PalladiumCleanup(FunTestScript):
    config = {}
    palladium_boot_up_obj = None
    dpcsh_proxy_obj = None

    def describe(self):
        self.set_test_details(steps="""
        1. Initialize objects and read boot up config
        """)

    def setup(self):
        global config, palladium_boot_up_obj, dpcsh_proxy_obj
        fun_test.log("In script setup")
        
        config = parse_file_to_json(ASSET_DIR + PALLADIUM_HOST_FILE)[0]
        fun_test.log("Palladium Host Config: %s" % config)

        palladium_boot_up_obj = Palladium(ip=config['boot_up_server_ip'],
                                          model=config['model'],
                                          design=config['design'])

        dpcsh_proxy_obj = DpcshProxy(ip=config['dpcsh_tcp_proxy_ip'],
                                     port=config['dpcsh_tcp_proxy_port'],
                                     usb=config['dpcsh_usb'])

    def run(self):
        fun_test.log("In script run")

    def cleanup(self):
        fun_test.log("In script cleanup")
        

class TestCase1(FunTestCase):
    
    def describe(self):
        self.set_test_details(id=1, summary="Release Palladium boards and stop dpcsh",
                              steps="""
                              1. Halt FunOS by executing dpc_shutdown cmd
                              2. Cleanup palladium resources and release boards
                              3. Ensure boards are released by the user
                              4. Stop DpcProxy
                              """)

    def setup(self):
        fun_test.log("In test case setup")

    def run(self):

        checkpoint = "Halt FunOS by executing dpc_shutdown cmd"
        result = dpcsh_proxy_obj.run_dpc_shutdown()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Cleanup palladium resources and release boards"
        result = palladium_boot_up_obj.cleanup_job()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Ensure boards are released by the user"
        result = palladium_boot_up_obj.ensure_boards_released()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Stop Dpcproxy"
        result = dpcsh_proxy_obj.stop()
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")


if __name__ == '__main__':
    ts = PalladiumCleanup()
    ts.add_test_case(TestCase1())
    ts.run()


