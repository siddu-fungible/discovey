from lib.host.linux import *
from scripts.networking.funeth.funeth import Funeth
from lib.system.fun_test import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth.sanity import Funeth
from lib.templates.storage.storage_fs_template import FunCpDockerContainer


def verify_host_pcie_link(hostname, username="localadmin", password="Precious1*", mode="x16", reboot=False,
                          retry_by_powercycle=False):
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
                if not retry_by_powercycle:
                    reboot_count = 2
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
        rdma_op = linux_obj.command(command="lsmod | grep funrdma")
        if "funrdma" in rdma_op:
            funrdma_rm = linux_obj.sudo_command("rmmod funrdma")
            result = "ERROR" not in funrdma_rm
            critical_log(expression=result, message="FunRDMA removed succesfully")
            if not result:
                return False
        funeth_op = linux_obj.command(command="lsmod | grep funeth")
        if "funeth" not in funeth_op:
            return True
        else:
            funeth_rm = linux_obj.sudo_command("rmmod funeth")
            result = "ERROR" not in funeth_rm
            critical_log(expression=result, message="Funeth removed succesfully")
            if result:
                return True
            else:
                return False
    except:
        return False


def power_cycle_host(hostname):
    linux_obj = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
    fun_test.log("Preparing to power cycle host %s " % hostname)
    linux_obj.sudo_command("ipmitool -I lanplus -H %s-ilo -U ADMIN -P ADMIN chassis power off" % hostname)
    fun_test.sleep(message="Waiting for host to go down", seconds=15)
    linux_obj.sudo_command("ipmitool -I lanplus -H %s-ilo -U ADMIN -P ADMIN chassis power on" % hostname)


def test_host_pings(host, ips, username="localadmin", password="Precious1*", strict=False, ping_interval=1,
                    ping_count=5):
    fun_test.log("")
    fun_test.log("================")
    fun_test.log("Pings from Hosts")
    fun_test.log("================")
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    linux_obj.command(command="ifconfig -a")
    for hosts in ips:
        ping_timeout = 60
        if ping_count > ping_timeout:
            ping_timeout = ping_count+10
        result = True
        output = linux_obj.command(command="sudo ping %s -i %s -c %s -q" % (hosts, ping_interval, ping_count),
                                   timeout=ping_timeout)
        m = re.search(r'(\d+)%\s+packet\s+loss', output)
        if m:
            percentage_loss = int(m.group(1))
            if percentage_loss <= 1:
                result &= True
            else:
                result &= False

        if result:
            fun_test.log("%s can reach %s" % (host, hosts))
        else:
            if strict:
                fun_test.test_assert(False, 'Cannot ping host')
            else:
                fun_test.critical("%s cannot reach %s" % (host, hosts))
    linux_obj.disconnect()


def setup_nu_host(funeth_obj):
    if not funeth_obj.nu_hosts:
        return
    for nu in funeth_obj.nu_hosts:
        linux_obj = funeth_obj.linux_obj_dict[nu]

        fun_test.test_assert(linux_obj.is_host_up(), 'NU host {} is up'.format(linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_interfaces(nu), 'Configure NU host {} interface'.format(
            linux_obj.host_ip))
        fun_test.test_assert(funeth_obj.configure_ipv4_routes(nu, configure_gw_arp=False),
                             'Configure NU host {} IPv4 routes'.format(
            linux_obj.host_ip))


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

        critical_log(funeth_obj.enable_multi_queues(hu, num_queues_tx=num_queues, num_queues_rx=num_queues),
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

        critical_log(funeth_obj.enable_multi_queues(hu, num_queues_tx=num_queues, num_queues_rx=num_queues),
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


def ensure_hping_install(host_ip, host_username, host_password):
    result = False
    linux_obj = Linux(host_ip=host_ip, ssh_username=host_username, ssh_password=host_password)
    try:
        cmd = "hping3 -v"
        output = linux_obj.sudo_command(command=cmd, timeout=40)
        if re.search(r'.*version.*', output):
            result = True
        else:
            install_cmd = "apt install hping3 -y"
            linux_obj.sudo_command(command=install_cmd, timeout=60)
            output = linux_obj.sudo_command(command=cmd, timeout=40)
            if re.search(r'.*version.*', output):
                result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    finally:
        linux_obj.disconnect()
    return result



def configure_vms(server_name, vm_dict):

    host_file = ASSET_DIR + "/hosts.json"
    all_hosts_specs = parse_file_to_json(file_name=host_file)
    host_spec = all_hosts_specs[server_name]
    linux_obj = Linux(host_ip=host_spec["host_ip"], ssh_username=host_spec["ssh_username"],
                      ssh_password=host_spec["ssh_password"])
    all_vms = map(lambda s: s.strip(), linux_obj.command(command="virsh list --all --name").split())
    linux_obj.command(command="sudo chmod 777 /dev/vfio/vfio")
    linux_obj.command(command="lspci -d 1dad:")
    for vm in vm_dict:
        if vm in all_vms:
            try:
                pci_device = linux_obj.command(command="virsh nodedev-list | grep %s" % vm_dict[vm]["ethernet_pci_device"])
                pci_device_pf2 = linux_obj.command(command="virsh nodedev-list | grep %s" % vm_dict[vm]["nvme_pci_device"])
                if vm_dict[vm]["ethernet_pci_device"] not in pci_device and vm_dict[vm]["nvme_pci_device"] not in pci_device_pf2:
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
                # fun_test.sleep(message="Waiting for VFs detach", seconds=1)
                start_op = linux_obj.command(command="virsh start %s" % vm, timeout=300)
                critical_log(("%s started" % vm) in start_op, message="VM %s started" % vm)
            except Exception as ex:
                if ex == "Timeout exceeded.":
                    fun_test.critical("Error with VM %s, proceeding" % vm)

        else:
            fun_test.critical(message="VM:%s is not installed on %s" % (vm, server_name))


def shut_all_vms(hostname):

    host_file = ASSET_DIR + "/hosts.json"
    all_hosts_specs = parse_file_to_json(file_name=host_file)
    host_spec = all_hosts_specs[hostname]
    linux_obj = Linux(host_ip=host_spec["host_ip"], ssh_username=host_spec["ssh_username"],
                      ssh_password=host_spec["ssh_password"])
    if linux_obj.check_ssh():
        linux_obj.command(command="for i in $(virsh list --name); do virsh shutdown $i; done")
    else:
        fun_test.critical(message="Cannot ssh into host %s" % host_spec["host_ip"])


def local_volume_create(storage_controller, vm_dict, uuid, count):
    result = storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                              capacity=vm_dict["blt_vol_capacity"],
                                              block_size=vm_dict["blt_vol_block_size"],
                                              uuid=uuid, name="thin_blk" + str(count),
                                              command_duration=vm_dict["command_timeout"])

    critical_log(result["status"], "Creating volume with uuid {}".format(uuid))

def local_encrypted_volume_create(storage_controller, vm_dict, uuid, count, xts_key, xts_tweak):
    result = storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                              capacity=vm_dict["blt_vol_capacity"],
                                              block_size=vm_dict["blt_vol_block_size"],
                                              encrypt=True,
                                              key=xts_key,
                                              xtweak=xts_tweak,
                                              uuid=uuid, name="thin_blk" + str(count),
                                              command_duration=vm_dict["command_timeout"])
    fun_test.log(result)
    critical_log(result["status"], "Creating encrypted volume with uuid {}".format(uuid))


def remote_storage_config(storage_controller, vm_dict, vol_uuid, count, ctrl_uuid, local_ip, local_port):
    local_volume_create(storage_controller, vm_dict, vol_uuid, count)

    print("\n")
    print("==============================================")
    print("Attaching Local Volume to Controller on remote DPU")
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


def enable_nvme_vfs(host, username="localadmin", password="Precious1*", pcie_vfs_count=32):
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    if not linux_obj.check_ssh():
        return False
    bdf = linux_obj.sudo_command("lspci -D -d 1dad: | grep 'Non-Volatile memory controller' | awk '{print $1}'").strip()
    linux_obj.sudo_command(command="echo \"%s\" >  /sys/bus/pci/devices/{}/sriov_numvfs".format(str(bdf))
                                   % pcie_vfs_count)
    fun_test.sleep(message="waiting for NVME VFs to be created")
    lspci_op = linux_obj.command(command="lspci -d 1dad:")
    if lspci_op.count("Non-Volatile memory controller:") >= pcie_vfs_count+1:
        return True
    else:
        return False


def check_nvme_driver(vm_dict, parallel=False):
    threads_list = []
    if parallel:
        for vm in vm_dict:

            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=_nvme_driver,
                                                      host=vm_dict[vm]["hostname"], name=vm,
                                                      password=vm_dict[vm]["password"], username=vm_dict[vm]["user"])
            threads_list.append(thread_id)
        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
    if not parallel:
        for vm in vm_dict:
            critical_log(_nvme_driver(host=vm_dict[vm]["hostname"], name=vm, password=vm_dict[vm]["password"],
                                      username=vm_dict[vm]["user"]), message="Check NVMe driver")


def ping_all_vms(vm_dict, parallel=False):
    # test_host_pings(host, ips, username="localadmin", password="Precious1*", strict=False)
    threads_list = []
    if parallel:
        for vm in vm_dict:
            if "vm_pings" in vm_dict[vm]:
                thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=test_host_pings,
                                                          host=vm_dict[vm]["hostname"], ips=vm_dict[vm]["vm_pings"],
                                                          password=vm_dict[vm]["password"],
                                                          username=vm_dict[vm]["user"])
                threads_list.append(thread_id)
        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
    if not parallel:
        for vm in vm_dict:
            if "vm_pings" in vm_dict[vm]:
                test_host_pings(host=vm_dict[vm]["hostname"], ips=vm_dict[vm]["vm_pings"],
                                password=vm_dict[vm]["password"], username=vm_dict[vm]["user"])


def fio_all_vms(vm_dict, parallel=False):
    threads_list = []
    if parallel:
        for vm in vm_dict:
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=test_host_fio,
                                                      host=vm_dict[vm]["hostname"],
                                                      password=vm_dict[vm]["password"],
                                                      username=vm_dict[vm]["user"])
            threads_list.append(thread_id)
        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
    if not parallel:
        for vm in vm_dict:
            test_host_fio(host=vm_dict[vm]["hostname"], password=vm_dict[vm]["password"], username=vm_dict[vm]["user"])


def _nvme_driver(host, name, password="Precious1*", username="localadmin"):
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)
    if not linux_obj.check_ssh():
        return False
    try:
        nvme_list = linux_obj.sudo_command(command="nvme list")
        if "nvme" not in nvme_list:
            nvme_lsmod = linux_obj.command(command="lsmod | grep nvme")
            if "nvme" in nvme_lsmod:
                linux_obj.sudo_command(command="rmmod nvme")
            linux_obj.sudo_command(command="modprobe nvme")
        nvme_list = linux_obj.command(command="sudo nvme list")
        critical_log(expression="nvme" in nvme_list, message="%s can see nvme drive" % name)
        return True
    except:
        return False


def cc_sanity_pings(docker_names, vlan_ips, fs_spec, nu_hosts, hu_hosts_0, hu_hosts_1, ping_count=10000,
                    ping_interval=0.005):
    result = True
    for docker in docker_names:
        container = FunCpDockerContainer(name=docker, host_ip=fs_spec['come']['mgmt_ip'],
                                         ssh_username=fs_spec['come']['mgmt_ssh_username'],
                                         ssh_password=fs_spec['come']['mgmt_ssh_password'])
        for nu_host in nu_hosts:
            # result &= container.ping(dst=nu_host, count=ping_count, max_percentage_loss=1, timeout=60,
            #                          interval=ping_interval, sudo=True)
            output = container.command(command="sudo ping -I %s %s -i %s -c %s -q" % (vlan_ips[docker], nu_host,
                                                                                   ping_interval, ping_count),
                                       timeout=300)
            m = re.search(r'(\d+)%\s+packet\s+loss', output)
            if m:
                percentage_loss = int(m.group(1))
                if percentage_loss <= 1:
                    result &= True
                else:
                    result &= False
            container.disconnect()
        if docker.split("-")[-1] == "0":
            for hu_host in hu_hosts_0:
                container = FunCpDockerContainer(name=docker, host_ip=fs_spec['come']['mgmt_ip'],
                                                 ssh_username=fs_spec['come']['mgmt_ssh_username'],
                                                 ssh_password=fs_spec['come']['mgmt_ssh_password'])
                # result &= container.ping(dst=hu_host, count=ping_count, max_percentage_loss=1, timeout=60,
                #                          interval=ping_interval, sudo=True)
                output = container.command(command="sudo ping -I %s %s -i %s -c %s -q" % (vlan_ips[docker], hu_host,
                                                                                       ping_interval, ping_count),
                                           timeout=300)
                m = re.search(r'(\d+)%\s+packet\s+loss', output)
                if m:
                    percentage_loss = int(m.group(1))
                    if percentage_loss <= 1:
                        result &= True
                    else:
                        result &= False

                container.disconnect()
        elif docker.split("-")[-1] == "1":
            for hu_host in hu_hosts_1:
                container = FunCpDockerContainer(name=docker, host_ip=fs_spec['come']['mgmt_ip'],
                                                 ssh_username=fs_spec['come']['mgmt_ssh_username'],
                                                 ssh_password=fs_spec['come']['mgmt_ssh_password'])
                # result &= container.ping(dst=hu_host, count=ping_count, max_percentage_loss=1, timeout=60,
                #                          interval=ping_interval, sudo=True)
                output = container.command(command="sudo ping -I %s %s -i %s -c %s -q" % (vlan_ips[docker], hu_host,
                                                                                       ping_interval, ping_count),
                                           timeout=300)
                m = re.search(r'(\d+)%\s+packet\s+loss', output)
                if m:
                    percentage_loss = int(m.group(1))
                    if percentage_loss <= 1:
                        result &= True
                    else:
                        result &= False
                container.disconnect()
    return result

def cc_dmesg(come_linux_obj, docker_names, fs_spec, path='/scratch/opt/fungible/logs'):
    fun_test.log('cc_dmesg(%s)' % str(docker_names))
    for docker in docker_names:
        out_file = '%s/CC_dmesg_%s.log' % (path, docker)
        cmd_prefix = 'docker exec %s bash -c' % (docker)
        cmd = '%s "dmesg" > %s' % (cmd_prefix, out_file)
        fun_test.log('cc_dmesg: %s %s %s' % (docker, out_file, cmd))
        come_linux_obj.command(cmd)

def cc_ethtool_stats_fpg_all(come_linux_obj, docker_names, fs_spec, path='/scratch/opt/fungible/logs'):
    fun_test.log('cc_ethtool(%s)' % str(docker_names))
    for docker in docker_names:
        out_file = '%s/CC_ethtool_%s.log' % (path, docker)
        cmd_prefix = 'docker exec %s bash -c' % (docker)
        come_linux_obj.command('touch %s' % out_file)

        for fpg in range(0, 24):
            cmd = '%s "echo ethtool fpg%s" >> %s' % (cmd_prefix, fpg, out_file)
            come_linux_obj.command(cmd)
            cmd = '%s "ethtool -S fpg%s" >> %s' % (cmd_prefix, fpg, out_file)
            fun_test.log('cc_ethtool: %s %s %s' % (docker, out_file, cmd))
            come_linux_obj.command(cmd)
            cmd = '%s "echo" >> %s' % (cmd_prefix, out_file)
            come_linux_obj.command(cmd)

def test_scp(source_host, dest_host, source_data_ip, dest_data_ip):
    result = True
    host_file = ASSET_DIR + "/hosts.json"
    all_hosts_specs = parse_file_to_json(file_name=host_file)
    source_host_spec = all_hosts_specs[source_host]
    dest_host_spec = all_hosts_specs[dest_host]
    source_linux = Linux(host_ip=source_host_spec["host_ip"], ssh_username=source_host_spec["ssh_username"],
                         ssh_password=source_host_spec["ssh_password"])
    dest_linux = Linux(host_ip=dest_host_spec["host_ip"], ssh_username=dest_host_spec["ssh_username"],
                         ssh_password=dest_host_spec["ssh_password"])
    dest_linux.sudo_command("cd ~; rm -fr scp_test;")
    dest_linux.command("cd ~; mkdir scp_test;")
    dest_linux.disconnect()
    source_linux.sudo_command("cd ~; rm -fr scp_test")
    source_linux.command("cd ~; mkdir scp_test; cd ~/scp_test")
    source_linux.dd(input_file="/dev/zero", output_file="scp_test_file_source.txt", count=1048576, block_size=100,
                    timeout=120, sudo=True)
    source_linux.scp(source_file_path="~/scp_test/scp_test_file_source.txt",
                     target_ip=dest_data_ip, target_file_path="~/scp_test/scp_test_file_dest.txt",
                     target_username=dest_host_spec["ssh_username"],
                     target_password=dest_host_spec["ssh_password"])

    op = dest_linux.command("ls ~/scp_test")
    if "scp_test_file_dest.txt" not in op:
        result = False
    critical_log(expression=result, message="SCP successful over data IP from %s to %s" % (source_host, dest_host))
    return result


def test_host_fio(host, username="localadmin", password="Precious1*", strict=False, filename="/dev/nvme0n1",
                  rw="readwrite", direct="1", bs="4k", ioengine="libaio", iodepth="16", name="local_fio_readwrite",
                  runtime="10"):
    if not strict:
        linux_obj = Linux(host_ip=host, username=username, password=password)
        fio_dict = linux_obj.fio(filename=filename, rw=rw, direct=direct, bs=bs, ioengine=ioengine, iodepth=iodepth,
                      name=name, runtime=runtime)
        critical_log(expression=fio_dict, message="Fio Result")


def reload_nvme_driver(host, username="localadmin", password="Precious1*", ns_id=1):
    host_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password,
                     connect_retry_timeout_max=60)
    host_obj.sudo_command("rmmod nvme; rmmod nvme_core", timeout=120)
    fun_test.sleep("Waiting for 10 seconds before loading driver", 10)
    host_obj.sudo_command("modprobe nvme")

    # Check if volume exists
    fun_test.sleep("Waiting for 5 seconds before checking lsblk", 5)
    lsblk_output = host_obj.lsblk()
    volume_name = "nvme0n" + str(ns_id)
    fun_test.test_assert(volume_name in lsblk_output, "{} device available".format(volume_name))
    fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                  message="{} device type check".format(volume_name))


def get_nvme_dev(host, username="localadmin", password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=username, ssh_password=password)

    # Get the BDF number for the F1 NVMe device
    bdf = linux_obj.sudo_command("lspci -D -d 1dad: | grep 'Non-Volatile memory controller' | awk '{print $1}'")

    # use bdf number to get the nvme char & block device
    nvme_char = linux_obj.sudo_command("ls /sys/bus/pci/devices/{}/nvme/".format(str(bdf)))
    nvme_cntlid = linux_obj.sudo_command("cat /sys/class/nvme/{}/cntlid".format(str(nvme_char)))
    ns_id = linux_obj.sudo_command("cat /sys/class/nvme/{}/{}c{}*/nsid".
                                   format(str(nvme_char), str(nvme_char), str(nvme_cntlid)))
    nvme_device = "/dev/" + str(nvme_char) + str(ns_id)

    return nvme_device
