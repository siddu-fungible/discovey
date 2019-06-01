from lib.host.linux import *
from scripts.networking.funeth.funeth import Funeth


def verify_host_pcie_link(hostname, username="localadmin", password="Precious1*", mode="x16", reboot=True):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    if reboot:
        funeth_op=""
        funeth_op = linux_obj.command(command="lsmod | grep funeth")
        if "funeth" not in funeth_op:
            linux_obj.reboot()
        else:
            linux_obj_host = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
            linux_obj_host.ipmi_power_cycle(host=hostname)
            linux_obj_host.disconnect()
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


def setup_hu_host(funeth_obj, update_driver=True):
    funsdk_commit = funsdk_bld = driver_commit = driver_bld = None
    if update_driver:
        funeth_obj.setup_workspace()
        fun_test.test_assert(funeth_obj.lspci(check_pcie_width=True), 'Fungible Ethernet controller is seen.')
        update_src_result = funeth_obj.update_src(parallel=True)
        if update_src_result:
            funsdk_commit, funsdk_bld, driver_commit, driver_bld = update_src_result
        fun_test.test_assert(update_src_result, 'Update funeth driver source code.')
    fun_test.test_assert(funeth_obj.build(parallel=True), 'Build funeth driver.')
    if not funeth_obj.load(sriov=4):
        fun_test.critical(message="Could not load funeth driver")
    else:
        funtest.log("Driver loaded on all hosts")
    
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]

        fun_test.test_assert(funeth_obj.enable_multi_txq(hu, num_queues=8),
                             'Enable HU host {} funeth interfaces multi Tx queues: 8.'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(hu, configure_gw_arp=(False)),
                             'Configure HU host {} IPv4 routes.'.format(
            linux_obj.host_ip))
        #fun_test.test_assert(funeth_obj.loopback_test(packet_count=80),
        #                    'HU PF and VF interface loopback ping test via NU')

    return funsdk_commit, funsdk_bld, driver_commit, driver_bld 

def rmmod_funeth_host(hostname, username="localadmin", password="Precious1*"):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    funeth_op = ""
    funeth_op = linux_obj.command(command="lsmod | grep funeth")
    if "funeth" not in funeth_op:
        return True
    else:
        funeth_rm = linux_obj.sudo_command("rmmod funeth")
        fun_test.test_assert(expression="ERROR" not in funeth_rm, message="Funeth removed succesfully")
        return True
