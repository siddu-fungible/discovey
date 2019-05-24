from lib.host.linux import *
from scripts.networking.funeth.funeth import Funeth


def verify_host_pcie_link(hostname, username="localadmin", password="Precious1*", mode="x16", reboot=True):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    if reboot:
        try:
            rm_funeth = linux_obj.sudo_command(command="rmmod funeth", timeout=60)
            fun_test.test_assert("ERROR" not in rm_funeth, message="rmmod funeth succesful")
        except:
            funeth_op = linux_obj.command(command="lsmod | grep funeth")
            fun_test.test_assert(expression="funeth" not in funeth_op, message="funeth not loaded.")
        linux_obj.command(command="echo 'funeth removed'")
        linux_obj.reboot()
        count = 0
        while not linux_obj.check_ssh():
            fun_test.sleep(message="waiting for server to come back up", seconds=15)
            count += 1
            if count == 5:
                fun_test.test_assert(expression=False, message="Cant reboot server %s" % hostname)
    else:
        count = 0
        while not linux_obj.check_ssh():
            fun_test.sleep(message="waiting for server to come back up", seconds=30)
            count += 1
            if count == 5:
                fun_test.test_assert(expression=False, message="Cant reach server %s" % hostname)

    lspci_out = linux_obj.sudo_command(command="sudo lspci -d 1dad: -vv | grep LnkSta")
    result = "1"
    if mode not in lspci_out:
        if "LnkSta" not in lspci_out:
            fun_test.critical("PCIE link did not come up")
            result = "0"
        else:
            fun_test.critical("PCIE link did not come up in %s mode" % mode)
            result = "2"
    return result


def setup_hu_host(funeth_obj, update_driver=True, enable_tso=True):
    if update_driver:
        funeth_obj.setup_workspace()
        fun_test.test_assert(funeth_obj.lspci(check_pcie_width=False), 'Fungible Ethernet controller is seen.')
        fun_test.test_assert(funeth_obj.update_src(), 'Update funeth driver source code.')
        fun_test.test_assert(funeth_obj.build(), 'Build funeth driver.')
        fun_test.test_assert(funeth_obj.load(sriov=4), 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]
        if enable_tso:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=False),
                                 'Enable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))
        else:
            fun_test.test_assert(funeth_obj.enable_tso(hu, disable=True),
                                 'Disable HU host {} funeth interfaces TSO.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.enable_multi_txq(hu, num_queues=8),
                             'Enable HU host {} funeth interfaces multi Tx queues: 8.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(hu), 'Configure HU host {} IPv4 routes.'.format(
            linux_obj.host_ip))
        #fun_test.test_assert(funeth_obj.loopback_test(packet_count=80),
        #                    'HU PF and VF interface loopback ping test via NU')