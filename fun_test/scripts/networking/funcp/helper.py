from lib.host.linux import *
from scripts.networking.funeth.funeth import Funeth


def verify_host_pcie_link(hostname, username="localadmin", password="Precious1*", mode="x16", reboot=False):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    if reboot:
        count = 1
        while True:
            count += 1
            response = os.system("ping -c 1 " + hostname)
            if count > 10:
                fun_test.critical(message="cannot ping host %s" % hostname)
                break
            if response == 0:
                if not linux_obj.check_ssh():
                    power_cycle_host(hostname)
                    fun_test.sleep(message="Waiting for host after power cycle", seconds=90)
                    break
                else:
                    break
            else:
                fun_test.log("Cannot ping host")
                fun_test.sleep(seconds=10, message="waiting for host")
        funeth_op = ""
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

    result = "1"
    reboot_count = 1
    while True:
        lspci_out = linux_obj.sudo_command(command="sudo lspci -d 1dad: -vv | grep LnkSta")
        if mode not in lspci_out:
            if "LnkSta" not in lspci_out:
                fun_test.critical("PCIE link did not come up")
                result = "0"
                if reboot_count < 2:
                    reboot_count += 1
                    power_cycle_host(hostname)
                    fun_test.sleep(message="Waiting for host after power cycle", seconds=90)
                    retries = 0
                    while not linux_obj.check_ssh():
                        fun_test.sleep(message="Waiting for host after power cycle", seconds=15)
                        retries += 1
                        if retries > 10:
                            break
                    continue
                else:
                    result = "0"
                    break
            else:
                fun_test.critical("PCIE link did not come up in %s mode" % mode)
                output = linux_obj.command('lspci -d 1dad:')
                critical_log(re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output),
                             message="Check ethernet device")
                result = "2"
                break
        else:
            output = linux_obj.command('lspci -d 1dad:')
            critical_log(re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output),
                         message="Check ethernet device")
            break
    return result


def rmmod_funeth_host(hostname, username="localadmin", password="Precious1*"):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    count = 1
    while True:
        count += 1
        response = os.system("ping -c 1 " + hostname)
        if count > 10:
            fun_test.critical("Cannot reach host")
            break
        if response == 0:
            if not linux_obj.check_ssh():
                power_cycle_host(hostname)
                fun_test.sleep(message="Waiting for host after power cycle", seconds=90)
            else:
                break
        else:
            fun_test.log("Cannot ping host")
            fun_test.sleep(seconds=15, message="waiting for host")
    funeth_op = ""
    try:
        funeth_op = linux_obj.command(command="lsmod | grep funeth")
        if "funeth" not in funeth_op:
            return True
        else:
            funeth_rm = linux_obj.sudo_command("rmmod funeth")
            critical_log(expression="ERROR" not in funeth_rm, message="Funeth removed succesfully")
            return True
    except:
        return False


def power_cycle_host(hostname):
    linux_obj = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
    fun_test.log("Preparing to power cycle host %s " % hostname)
    linux_obj.sudo_command("ipmitool -I lanplus -H %s-ilo -U ADMIN -P ADMIN chassis power off" % hostname)
    fun_test.sleep(message="Waiting for host to go down", seconds=15)
    linux_obj.sudo_command("ipmitool -I lanplus -H %s-ilo -U ADMIN -P ADMIN chassis power on" % hostname)


def test_host_pings(host, ips):
    fun_test.log("")
    fun_test.log("================")
    fun_test.log("Pings from Hosts")
    fun_test.log("================")
    linux_obj = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
    for hosts in ips:
        linux_obj.command(command="ifconfig -a")
        result = linux_obj.ping(dst=hosts)
        if result:
            fun_test.log("%s can reach %s" % (host, hosts))
        else:
            fun_test.critical("%s cannot reach %s" % (host, hosts))


def setup_hu_host(funeth_obj, update_driver=True):
    fun_test.log("===================")
    fun_test.log("Configuring HU host")
    fun_test.log("===================")
    funsdk_commit = funsdk_bld = driver_commit = driver_bld = None
    if update_driver:
        funeth_obj.setup_workspace()
        critical_log(funeth_obj.lspci(check_pcie_width=False), 'Fungible Ethernet controller is seen.')

        update_src_result = funeth_obj.update_src(parallel=True)
        if update_src_result:
            funsdk_commit, funsdk_bld, driver_commit, driver_bld = update_src_result
            critical_log(update_src_result, 'Update funeth driver source code.')
        fun_test.test_assert(funeth_obj.build(parallel=True), 'Build funeth driver.')
    critical_log(funeth_obj.load(sriov=4), 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]

        critical_log(funeth_obj.enable_multi_txq(hu, num_queues=8),
                     'Enable HU host {} funeth interfaces multi Tx queues: 8.'.format(linux_obj.host_ip))
        critical_log(funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(
            linux_obj.host_ip))
        critical_log(funeth_obj.configure_ipv4_routes(hu, configure_gw_arp=False),
                     'Configure HU host {} IPv4 routes.'.format(
                         linux_obj.host_ip))
        fun_test.log("==================================")
        fun_test.log("Configuration of HU host completed")
        fun_test.log("==================================")

    return funsdk_commit, funsdk_bld, driver_commit, driver_bld


def get_ethtool_on_hu_host(funeth_obj):
    for hu in funeth_obj.hu_hosts:
        fun_test.log("====================================")
        fun_test.log("Ethtool Stats after HU Configuration")
        fun_test.log("====================================")
        # funeth_obj.get_ethtool_stats(hu)
        bus = funeth_obj.get_bus_info_from_ethtool(hu)


def critical_log(expression, message):
    if expression:
        fun_test.test_assert(expression=expression, message=message)

    if not expression:
        fun_test.critical(message=message)
