from lib.system.fun_test import *
from lib.host.palladium import DpcshProxy, Palladium


PALLADIUM_HOST_FILE = "/palladium_hosts.json"

config = {}
palladium_boot_up_obj = None
dpcsh_proxy_obj = None
is_cleanup_needed = True


class PalladiumBringup(FunTestScript):
    
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

    def cleanup(self):
        fun_test.log("In script cleanup")


class TestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1, summary="Load Palladium Image",
                              steps="""
                              1. Read Palladium host configs
                              2. Build Palladium image from master and pushed it to desired location
                              3. Boot up palladium with FunOS image
                              4. Start dpcsh in tcp proxy mode and ensure dpcsh is started
                              """)

    def setup(self):
        fun_test.log("In test case setup")

        global is_cleanup_needed

        checkpoint = "Boot up palladium with FunOS design %s Model %s" % (config['design'],
                                                                          config['model'])
        result = palladium_boot_up_obj.boot()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Start dpcsh with %s in tcp proxy mode" % config['dpcsh_usb']
        result = dpcsh_proxy_obj.start()
        fun_test.test_assert(result, checkpoint)

        is_cleanup_needed = False

        checkpoint = "Ensure dpcsh started in TCP proxy mode"
        result = dpcsh_proxy_obj.ensure_started()
        fun_test.test_assert(result, checkpoint)

    def run(self):
        fun_test.log("In test case run")

    def cleanup(self):
        if is_cleanup_needed:
            palladium_boot_up_obj.cleanup_job()


if __name__ == '__main__':
    ts = PalladiumBringup()
    ts.add_test_case(TestCase1())
    ts.run()

