from lib.host.network_controller import *


dpc_proxy_ip = "10.1.21.120"
dpc_proxy_port = 42221
try:
    fun_test.log("Connecting to Remote DPC %s on port %d" % (dpc_proxy_ip, dpc_proxy_port))
    network_controller_obj = NetworkController(dpc_server_ip=dpc_proxy_ip, dpc_server_port=dpc_proxy_port,
                                               verbose=True)

    psw_stats = network_controller_obj.peek_psw_global_stats()
    print psw_stats

    network_controller_obj.echo_hello()

except Exception as ex:
    print ex

