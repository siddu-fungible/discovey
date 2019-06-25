from lib.host.linux import *
from scripts.networking.funeth.funeth import Funeth
from lib.system.fun_test import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth.sanity import Funeth


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


def test_host_pings(host, ips, username="localadmin", password="Precious1*"):
    fun_test.log("")
    fun_test.log("================")
    fun_test.log("Pings from Hosts")
    fun_test.log("================")
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    for hosts in ips:
        linux_obj.command(command="ifconfig -a")
        result = linux_obj.ping(dst=hosts)
        if result:
            fun_test.log("%s can reach %s" % (host, hosts))
        else:
            fun_test.critical("%s cannot reach %s" % (host, hosts))


def setup_hu_host(funeth_obj, update_driver=True, sriov=4, num_queues=4):
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
    critical_log(funeth_obj.load(sriov=sriov, num_queues=num_queues), 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]

        critical_log(funeth_obj.enable_multi_txq(hu, num_queues=4),
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


def setup_hu_vm(funeth_obj, update_driver=True, sriov=0, num_queues=1):
    fun_test.log("==========================")
    fun_test.log("Configuring VM on HU Host")
    fun_test.log("==========================")
    funsdk_commit = funsdk_bld = driver_commit = driver_bld = None
    if update_driver:
        funeth_obj.setup_workspace()
        critical_log(funeth_obj.lspci(check_pcie_width=False), 'Fungible Ethernet controller is seen.')
        update_src_result = funeth_obj.update_src(parallel=True)
        if update_src_result:
            funsdk_commit, funsdk_bld, driver_commit, driver_bld = update_src_result
            critical_log(update_src_result, 'Update funeth driver source code.')
        fun_test.test_assert(funeth_obj.build(parallel=True), 'Build funeth driver.')
    critical_log(funeth_obj.load(sriov=sriov, num_queues=num_queues), 'Load funeth driver.')
    for hu in funeth_obj.hu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[hu]

        critical_log(funeth_obj.enable_multi_txq(hu, num_queues=8),
                     'Enable HU host {} funeth interfaces multi Tx queues: 8.'.format(linux_obj.host_ip))
        critical_log(funeth_obj.configure_interfaces(hu), 'Configure HU host {} funeth interfaces.'.format(
            linux_obj.host_ip))
        critical_log(funeth_obj.configure_ipv4_routes(hu, configure_gw_arp=False),
                     'Configure HU host {} IPv4 routes.'.format(
                         linux_obj.host_ip))
        fun_test.log("=============================")
        fun_test.log("Configuration of VM completed")
        fun_test.log("=============================")

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


def configure_vms(server_name, vm_dict, yml, update_funeth_driver=False, pcie_vfs_count=32):
    host_file = ASSET_DIR + "/hosts.json"
    all_hosts_specs = parse_file_to_json(file_name=host_file)
    host_spec = all_hosts_specs[server_name]
    linux_obj = Linux(host_ip=host_spec["host_ip"], ssh_username=host_spec["ssh_username"],
                      ssh_password=host_spec["ssh_password"])
    all_vms = map(lambda s: s.strip(), linux_obj.command(command="virsh list --all --name").split())
    linux_obj.command(command="sudo chmod 777 /dev/vfio/vfio")
    linux_obj.sudo_command(command="echo \"%s\" >  /sys/bus/pci/devices/0000\:af\:00.2/sriov_numvfs" % pcie_vfs_count)
    linux_obj.command(command="lspci -d 1dad:")
    for vm in vm_dict:
        if vm in all_vms:
            try:
                pci_device = linux_obj.command(command="virsh nodedev-list | grep %s" % vm_dict[vm]["ethernet_pci_device"])
                if vm_dict[vm]["ethernet_pci_device"] not in pci_device:
                    fun_test.critical(message="%s device not present on server" % vm_dict[vm]["ethernet_pci_device"])
                    fun_test.log("Skipping VM: %s" % vm)
                    continue
                shut_op = linux_obj.command(command="virsh shutdown %s" % vm)
                if not "domain is not running" in shut_op:
                    fun_test.sleep(message="Waiting for VM to shutdown", seconds=7)
                linux_obj.command(command="virsh nodedev-dettach %s" % vm_dict[vm]["ethernet_pci_device"])
                if "nvme_pci_device" in vm_dict[vm]:
                    pci_device_nvme = linux_obj.command(
                        command="virsh nodedev-list | grep %s" % vm_dict[vm]["nvme_pci_device"])
                    critical_log(expression=vm_dict[vm]["nvme_pci_device"] in pci_device_nvme,
                                 message="Check NVME PF %s is present" % vm_dict[vm]["nvme_pci_device"])
                    if vm_dict[vm]["nvme_pci_device"] in pci_device_nvme:
                        linux_obj.command(command="virsh nodedev-dettach %s" % vm_dict[vm]["nvme_pci_device"])
                fun_test.sleep(message="Waiting for VFs detach")
                start_op = linux_obj.command(command="virsh start %s" % vm)
                critical_log(("%s started" % vm) in start_op, message="VM %s started" % vm)
            except Exception as ex:
                if ex == "Timeout exceeded.":
                    fun_test.critical("Error with VM %s, proceeding" % vm)

        else:
            fun_test.critical(message="VM:%s is not installed on %s" % (vm, server_name))
    fun_test.sleep(message="Waiting for VMs to come up", seconds=120)

    tb_config_obj = tb_configs.TBConfigs(yml)
    funeth_obj = Funeth(tb_config_obj, ws='/home/localadmin/ws')
    fun_test.shared_variables['funeth_obj'] = funeth_obj
    setup_hu_vm(funeth_obj, update_driver=update_funeth_driver)


def shut_all_vms(hostname):

    host_file = ASSET_DIR + "/hosts.json"
    all_hosts_specs = parse_file_to_json(file_name=host_file)
    host_spec = all_hosts_specs[hostname]
    linux_obj = Linux(host_ip=host_spec["host_ip"], ssh_username=host_spec["ssh_username"],
                      ssh_password=host_spec["ssh_password"])
    linux_obj.command(command="for i in $(virsh list --name); do virsh shutdown $i; done")


def local_volume_create(storage_controller, vm_dict, uuid, count):
    result = storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                              capacity=vm_dict["blt_vol_capacity"],
                                              block_size=vm_dict["blt_vol_block_size"],
                                              uuid=uuid, name="thin_blk" + str(count),
                                              command_duration=vm_dict["command_timeout"])

    critical_log(result["status"], "Creating volume with uuid {}".format(uuid))


def remote_storage_config(storage_controller, vm_dict, vol_uuid, count, ctrl_uuid, local_ip, local_port):
    local_volume_create(storage_controller, vm_dict, vol_uuid, count)

    print("\n")
    print("==============================================")
    print("Attaching Local Volume to Controller on DPU 1")
    print("==============================================\n")
    result = storage_controller.attach_volume_to_controller(ctrlr_uuid=ctrl_uuid,
                                                            vol_uuid=vol_uuid,
                                                            ns_id=int(count),
                                                            command_duration=vm_dict["command_timeout"])
    fun_test.log(result)
    critical_log(result["status"], "Attaching volume {} to controller {}".format(vol_uuid, ctrl_uuid))


def rds_volume_create(storage_controller, vm_dict, vol_uuid, count, remote_ip, port):
    command_result = storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                      capacity=vm_dict["rds_vol_capacity"],
                                                      block_size=vm_dict["rds_vol_block_size"],
                                                      uuid=vol_uuid,
                                                      name="rds-block"+str(count),
                                                      remote_nsid=int(count),
                                                      remote_ip=remote_ip,
                                                      port=port,
                                                      command_duration=vm_dict["command_timeout"])
    critical_log(command_result["status"], "Creating volume with uuid {}".format(vol_uuid))


def check_nvme_function(host, username="localadmin", password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    if not linux_obj.check_ssh():
        return False
    lspci_op = linux_obj.command("lspci -d 1dad:")
    return "Non-Volatile memory controller" in lspci_op


def check_funeth_function(host, username="localadmin", password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    if not linux_obj.check_ssh():
        return False
    lspci_op = linux_obj.command("lspci -d 1dad:")
    return "Ethernet controller" in lspci_op
