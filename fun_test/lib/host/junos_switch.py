from lib.system.fun_test import fun_test
from lib.host.linux import Linux


class JunOsSwitch(Linux):
    def post_init(self):
        self.set_root_prompt_terminator("% ")
        self._connect()

    def enter_cli(self):
        self.set_prompt_terminator("> ")
        self.command("cli")

    def exit_cli(self):
        self.set_prompt_terminator("% ")
        self.command("exit")

    def enter_configure(self):
        self.set_prompt_terminator("# ")
        self.command("configure")

    def exit_configure(self):
        self.set_prompt_terminator("> ")
        self.command("exit")


if __name__ == "__main2__":
    router_obj = Router(host_ip="10.1.20.92", telnet_password="zebra", telnet_port=51111)

    router_obj.enable()
    output = router_obj.command("show interface")

    fun_test.log("\nOutput:" + output)

    router_obj.config()
    router_obj.command("""hostname john
    hostname john2
    """)

if __name__ == "__main__":
    router_obj = JunOsSwitch(host_ip="10.1.20.92", ssh_username="root", ssh_password="Precious1*")
    router_obj.enter_cli()
    output = router_obj.command("show interfaces et-0/0/28 brief ")
    router_obj.enter_configure()
    output = router_obj.command("run show interfaces et-0/0/28 brief")
    router_obj.exit_configure()
    router_obj.exit_cli()