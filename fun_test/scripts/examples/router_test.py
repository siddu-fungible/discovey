from lib.system.fun_test import *
from lib.host.router import Router

router_obj = Router(host_ip="10.1.20.67", telnet_password="zebra", telnet_port=51111)
router_obj.enable()
output = router_obj.command("show interface")

fun_test.log("\nOutput:" + output)
router_obj.config()
router_obj.command("hostname john")
router_obj.command("""
hostname john3
hostname john2
""")