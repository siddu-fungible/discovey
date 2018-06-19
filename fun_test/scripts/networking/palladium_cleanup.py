from lib.system.fun_test import *
from lib.host.palladium import Palladium, DpcshProxy

PALLADIUM_HOST_FILE = "/palladium_hosts.json"


class PalladiumCleanup(FunTestScript):
    config = {}
    palladium_boot_up_obj = None
    dpcsh_proxy_obj = None

    def describe(self):
        self.set_test_details(steps="""
        1. Halt FunOS based on the version
        2. Cleanup palladium resources and release boards
        3. Ensure boards are released by the user
        4. Stop DpcProxy
        """)

    def setup(self):
        fun_test.log("In script setup")
        self.config = parse_file_to_json(ASSET_DIR + PALLADIUM_HOST_FILE)[0]
        fun_test.log("Palladium Host Config: %s" % self.config)

        self.palladium_boot_up_obj = Palladium(ip=self.config['boot_up_server_ip'],
                                               model=self.config['model'],
                                               design=self.config['design'])

        self.dpcsh_proxy_obj = DpcshProxy(ip=self.config['dpcsh_tcp_proxy_ip'],
                                          port=self.config['dpcsh_tcp_proxy_port'],
                                          usb=self.config['dpcsh_usb'])

    def run(self):
        fun_test.log("In script run")

        checkpoint = "Halt FunOS based on the version"
        # TODO: Get FunOS version and halt accordingly

        checkpoint = "Cleanup palladium resources and release boards"
        result = self.palladium_boot_up_obj.cleanup_job()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Ensure boards are released by the user"
        # TODO: Confirm boards are released by regression user. Extend palladium host lib for this

        checkpoint = "Stop Dpcproxy"
        result = self.dpcsh_proxy_obj.stop()
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        fun_test.log("In script cleanup")


if __name__ == '__main__':
    ts = PalladiumCleanup()
    ts.run()


