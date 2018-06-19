from lib.system.fun_test import *
from lib.host.palladium import DpcshProxy, Palladium


PALLADIUM_HOST_FILE = "/palladium_hosts.json"


class PalladiumBringup(FunTestScript):
    config = {}
    palladium_boot_up_obj = None
    dpcsh_proxy_obj = None
    is_cleanup_needed = True

    def describe(self):
        self.set_test_details(steps="""
        1. Read Palladium host configs
        2. Build Palladium image from master and pushed it to desired location
        3. Boot up palladium with FunOS image
        4. Start dpcsh in tcp proxy mode and ensure dpcsh is started
        """)

    def setup(self):
        self.config = parse_file_to_json(ASSET_DIR + PALLADIUM_HOST_FILE)[0]
        fun_test.log("Palladium Host Config: %s" % self.config)

        self.palladium_boot_up_obj = Palladium(ip=self.config['boot_up_server_ip'],
                                               model=self.config['model'],
                                               design=self.config['design'])

        self.dpcsh_proxy_obj = DpcshProxy(ip=self.config['dpcsh_tcp_proxy_ip'],
                                          port=self.config['dpcsh_tcp_proxy_port'],
                                          usb=self.config['dpcsh_usb'])

        checkpoint = "Boot up palladium with FunOS design %s Model %s" % (self.config['design'],
                                                                          self.config['model'])
        result = self.palladium_boot_up_obj.boot()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Start dpcsh with %s in tcp proxy mode" % self.config['dpcsh_usb']
        result = self.dpcsh_proxy_obj.start()
        fun_test.test_assert(result, checkpoint)

        self.is_cleanup_needed = False

    def run(self):
        fun_test.log("In palladium bring up run")

        checkpoint = "Ensure dpcsh started in TCP proxy mode"
        result = self.dpcsh_proxy_obj.ensure_started()
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        if not self.is_cleanup_needed:
            self.palladium_boot_up_obj.cleanup_job()
    # TODO: Check script result here if it is fail then clean up the palladium resources


if __name__ == '__main__':
    ts = PalladiumBringup()
    ts.run()

