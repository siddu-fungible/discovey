from lib.system.fun_test import fun_test
from lib.host.linux import Linux


class Router(Linux):
    def post_init(self):
        self.use_telnet = True
        self.set_prompt_terminator(r'> ')
        self._connect()


    def _set_term_settings(self):
        return True

    def _set_paths(self):
        return True

    def enable(self):
        self.set_prompt_terminator(r'# ')
        self.command("en")

    def config(self):
        self.command("conf t")


if __name__ == "__main__":
    router_obj = Router(host_ip="10.1.20.67", telnet_password="zebra", telnet_port=51111)
    router_obj.enable()
    output = router_obj.command("show interface")

    fun_test.log("\nOutput:" + output)

    router_obj.config()
    router_obj.command("""hostname john
    hostname john2
    """)