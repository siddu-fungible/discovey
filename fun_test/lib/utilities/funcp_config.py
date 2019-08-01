from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import json
import random
import itertools
from scripts.networking.lib_nw import funcp
import socket
from lib.templates.storage.storage_fs_template import FunCpDockerContainer
import os


class FunControlPlaneBringup:

    def __init__(self, fs_name, boot_image_f1_0="funos-f1.stripped_retimer_test_vdd_delay.gz",
                 boot_image_f1_1="funos-f1.stripped_retimer_test_vdd_delay.gz", boot_args_f1_0=None,
                 boot_args_f1_1=None, hostprefix=None):
        self.fs_name = fs_name
        self.boot_image_f1_0 = boot_image_f1_0
        self.boot_image_f1_1 = boot_image_f1_1
        self.boot_args_f1_0 = boot_args_f1_0
        self.boot_args_f1_1 = boot_args_f1_1
        if not boot_args_f1_0:
            self.boot_args_f1_0 = "app=hw_hsu_test cc_huid=3 --all_100g --dpc-server --dpc-uart " \
                                  "--dis-stats --mgmt"

        if not boot_args_f1_1:
            self.boot_args_f1_1 = "app=hw_hsu_test cc_huid=2 --all_100g --dis-stats --dpc-server " \
                                  "--dpc-uart --mgmt"

        self.fs_spec = fun_test.get_asset_manager().get_fs_by_name(fs_name)
        self.fs_boot_number = None
        self.abstract_configs_f1_0 = None
        self.abstract_configs_f1_1 = None
        self.mpg_ips = {}
        self.docker_names = []
        self.vlan1_ips = {}
        self.vlan_ips_got = False
        self.docker_names_got = False
        self.hostprefix = hostprefix

    def boot_both_f1(self, power_cycle_come=True, reboot_come=True, gatewayip=None, funcp_cleanup=False):
        fs_0 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_0,
                      boot_args=self.boot_args_f1_0)
        fs_1 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_1,
                      boot_args=self.boot_args_f1_1)
        fun_test.simple_assert(fs_0, "Succesfully fetched image, credentials and bootargs")
        if funcp_cleanup:
            self.check_come_stuck(fs_obj=fs_0)
            self.cleanup_funcp()
        if fs_0.retimer_workround:
            fs_0._apply_retimer_workaround()
        fun_test.test_assert(fs_0.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs_0.set_f1s(), "Set F1s")
        fun_test.test_assert(fs_0.fpga_initialize(), "FPGA initiaize")

        fun_test.test_assert(fs_0.bmc.setup_serial_proxy_connection(f1_index=0),
                                 "Setup nc serial proxy connection")
        fun_test.test_assert(fs_0.bmc.u_boot_load_image(index=0, tftp_image_path=fs_0.tftp_image_path,
                                                        boot_args=fs_0.boot_args, gateway_ip=gatewayip),
                             "U-Bootup f1: {} complete".format(0))
        fs_0.bmc.start_uart_log_listener(f1_index=0, serial_device=None)
        fun_test.test_assert(fs_0.bmc.setup_serial_proxy_connection(f1_index=1),
                             "Setup nc serial proxy connection")
        fun_test.test_assert(
            fs_0.bmc.u_boot_load_image(index=1, tftp_image_path=fs_1.tftp_image_path, boot_args=fs_1.boot_args,
                                       gateway_ip=gatewayip),
            "U-Bootup f1: {} complete".format(1))
        fs_0.bmc.start_uart_log_listener(f1_index=1, serial_device=None)
        if reboot_come:
            fun_test.test_assert(fs_0.come_reset(power_cycle=True, non_blocking=True),
                                 "ComE rebooted successfully")
            fun_test.sleep(message="waiting for COMe", seconds=150)
            if power_cycle_come:
                come_ping_test = False

                come_ping_test_count = 0
                while not come_ping_test:
                    response = os.system("ping -c 1 " + self.fs_spec['come']['mgmt_ip'])
                    if response == 0:
                        come_ping_test = True
                    else:
                        fun_test.sleep(message="Waiting for COMe to be pingable", seconds=15)
                        come_ping_test_count += 0
                        if come_ping_test_count > 10:
                            fun_test.test_assert_expected(expected=True, actual=come_ping_test, message="Come ping test")
                            break
                ssh_test_come = fs_0.come.check_ssh()
                if not ssh_test_come:
                    fun_test.test_assert(fs_0.from_bmc_reset_come(), "BMC Reset COMe")
                    fun_test.sleep(message="Power cycling COMe", seconds=150)

            fun_test.test_assert(fs_0.come_initialize(), "ComE initialized")
            fun_test.test_assert(fs_0.come.detect_pfs(), "Fungible PFs detected")
            fun_test.test_assert(fs_0.come.setup_dpc(), "Setup DPC")
            fun_test.test_assert(fs_0.come.is_dpc_ready(), "DPC ready")
        return True

    def boot_f1_0(self, power_cycle_come=True, gatewayip=None, funcp_cleanup=False):
        fs_0 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_0,
                      boot_args=self.boot_args_f1_0, disable_f1_index=1)
        if funcp_cleanup:
            self.check_come_stuck(fs_obj=fs_0)
        fun_test.simple_assert(fs_0, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs_0.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs_0.set_f1s(), "Set F1s")
        fun_test.test_assert(fs_0.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs_0.bmc.setup_serial_proxy_connection(f1_index=0),
                                 "Setup nc serial proxy connection")
        fun_test.test_assert(fs_0.bmc.u_boot_load_image(index=0, tftp_image_path=fs_0.tftp_image_path,
                                                        boot_args=fs_0.boot_args, gateway_ip=gatewayip),
                             "U-Bootup f1: {} complete".format(0))
        fs_0.bmc.start_uart_log_listener(f1_index=0)
        fun_test.test_assert(fs_0.come_reset(power_cycle=True, non_blocking=True),
                             "ComE rebooted successfully")
        fun_test.sleep(message="waiting for COMe", seconds=90)
        if power_cycle_come:
            come_ping_test = False

            come_ping_test_count = 0
            while not come_ping_test:
                response = os.system("ping -c 1 " + self.fs_spec['come']['mgmt_ip'])
                if response == 0:
                    come_ping_test = True
                else:
                    fun_test.sleep(message="Waiting for COMe to be pingable", seconds=15)
                    come_ping_test_count += 0
                    if come_ping_test_count > 10:
                        fun_test.test_assert_expected(expected=True, actual=come_ping_test, message="Come ping test")
                        break
            ssh_test_come = fs_0.come.check_ssh()
            if not ssh_test_come:
                fun_test.test_assert(fs_0.from_bmc_reset_come(), "BMC Reset COMe")
                fun_test.sleep(message="Power cycling COMe", seconds=150)

        fun_test.test_assert(fs_0.come_initialize(), "ComE initialized")
        fun_test.test_assert(fs_0.come.detect_pfs(), "Fungible PFs detected")
        fun_test.test_assert(fs_0.come.setup_dpc(), "Setup DPC")
        fun_test.test_assert(fs_0.come.is_dpc_ready(), "DPC ready")

    def boot_f1_1(self, power_cycle_come=True, gatewayip=None, funcp_cleanup=False):
        fs = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_1,
                      boot_args=self.boot_args_f1_1, disable_f1_index=0)
        if funcp_cleanup:
            self.check_come_stuck(fs_obj=fs)
            self.cleanup_funcp()
        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs.set_f1s(), "Set F1s")
        fun_test.test_assert(fs.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs_0.bmc.setup_serial_proxy_connection(f1_index=1),
                             "Setup nc serial proxy connection")
        fun_test.test_assert(fs.bmc.u_boot_load_image(index=1, tftp_image_path=fs.tftp_image_path,
                                                        boot_args=fs.boot_args, gateway_ip=gatewayip),
                             "U-Bootup f1: {} complete".format(1))
        fs.bmc.start_uart_log_listener(f1_index=1)
        fun_test.test_assert(fs.come_reset(power_cycle=True, non_blocking=True),
                             "ComE rebooted successfully")
        fun_test.sleep(message="waiting for COMe", seconds=90)
        if power_cycle_come:
            come_ping_test = False

            come_ping_test_count = 0
            while not come_ping_test:
                response = os.system("ping -c 1 " + self.fs_spec['come']['mgmt_ip'])
                if response == 0:
                    come_ping_test = True
                else:
                    fun_test.sleep(message="Waiting for COMe to be pingable", seconds=15)
                    come_ping_test_count += 0
                    if come_ping_test_count > 10:
                        fun_test.test_assert_expected(expected=True, actual=come_ping_test, message="Come ping test")
                        break
            ssh_test_come = fs.come.check_ssh()
            if not ssh_test_come:
                fun_test.test_assert(fs.from_bmc_reset_come(), "BMC Reset COMe")
                fun_test.sleep(message="Power cycling COMe", seconds=150)

        fun_test.test_assert(fs.come_initialize(), "ComE initialized")
        fun_test.test_assert(fs.come.detect_pfs(), "Fungible PFs detected")
        fun_test.test_assert(fs.come.setup_dpc(), "Setup DPC")
        fun_test.test_assert(fs.come.is_dpc_ready(), "DPC ready")

    def bringup_funcp(self, prepare_docker=True, ep=False):
        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                               ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        ssh_test_come = linux_obj_come.check_ssh()
        fun_test.test_assert(expression=ssh_test_come, message="Make sure ssh can be done to COMe")
        come_lspci = linux_obj_come.lspci(grep_filter="1dad:")
        if prepare_docker:

            linux_obj_come.command(command="cd /mnt/keep/")
            linux_obj_come.sudo_command(command="rm -rf FunSDK")
            git_pull = linux_obj_come.command("git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK", timeout=120)
            linux_obj_come.command(command="cd /mnt/keep/FunSDK/")
            prepare_docker_output = linux_obj_come.command("./integration_test/emulation/test_system.py --prepare "
                                                           "--docker", timeout=1200)
            sections = ['Cloning into \'FunSDK\'', 'Cloning into \'fungible-host-drivers\'', 'Prepare End']
            for section in sections:
                fun_test.test_assert(section in prepare_docker_output, "{} seen".format(section))

        linux_obj_come.command(command="cd /mnt/keep/FunSDK/")
        fun_test.log("")
        fun_test.log("=========================")
        fun_test.log("Fun Control Plane Bringup")
        fun_test.log("=========================")
        setup_docker_command = "./integration_test/emulation/test_system.py --setup --docker"
        if self.hostprefix:
            setup_docker_command += " --hostprefix %s" % self.hostprefix
        if ep:
            setup_docker_output = linux_obj_come.command(command=(setup_docker_command + " --ep"), timeout=1200)
        else:
            setup_docker_output = linux_obj_come.command(command=setup_docker_command, timeout=1200)
        sections = ['Bring up Control Plane', 'Device 1dad:', 'move fpg interface to f0 docker',
                    'libfunq bind  End', 'move fpg interface to f1 docker', 'Bring up Control Plane dockers']
        for section in sections:
            fun_test.test_assert(section in setup_docker_output, "{} seen".format(section))
        linux_obj_come.disconnect()
        self._get_docker_names()
        if ep:
            for docker in self.docker_names:
                linux_obj_come.command("docker exec %s sudo ip link add link irb name vlan1 type vlan id 1" % docker)
                linux_obj_come.command("docker exec %s sudo ip link set vlan1 up" % docker)
        for docker in self.docker_names:
            container = FunCpDockerContainer(name=docker, host_ip=self.fs_spec['come']['mgmt_ip'],
                                              ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                              ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            op = container.command("ifconfig vlan1")
            fun_test.test_assert(expression="vlan1" in op, message="Make sure vlan1 is present on %s" % docker)
        return True

    def funcp_abstract_config(self, abstract_config_f1_0, abstract_config_f1_1, host_ip=None, workspace="/scratch",
                              ssh_username=None, ssh_password=None, update_funcp_folder=False):
        if self.mpg_ips == {}:
            self.fetch_mpg_ips()
        fun_test.test_assert(expression=self.mpg_ips != {}, message="MPG_IPs have been assigned")
        if host_ip and ssh_password and ssh_username:
            linux_obj = Linux(host_ip=host_ip, ssh_username= ssh_username, ssh_password=ssh_password)
        else:
            linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                              ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                              ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        # Make sure API server is active
        fun_test.test_assert(expression=linux_obj.get_process_id_by_pattern(process_pat="apisvr"),
                             message="API server active")

        if update_funcp_folder:
            # linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
            funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)
            fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
            # fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
            # Get FunControlPlane
        if abstract_config_f1_0:
            self.abstract_configs_f1_0 = fun_test.parse_file_to_json(abstract_config_f1_0)

        if abstract_config_f1_1:
            self.abstract_configs_f1_1 = fun_test.parse_file_to_json(abstract_config_f1_1)

        for f1 in self.mpg_ips:

            # ping MPG IPs before executing abstract config
            ping_mpg = linux_obj.ping(self.mpg_ips[f1])

            if not ping_mpg:
                fun_test.sleep(message="Waiting to retry mpg ping")
                ping_mpg = linux_obj.ping(self.mpg_ips[f1], count=15)

            fun_test.test_assert(expression=ping_mpg, message="Ping MPG IP %s from COMe" % self.mpg_ips[f1])

            file_contents = None
            file_name = str(f1).strip() + "_abstract.json"
            if str(f1.split("-")[-1]) == "0":
                self.abstract_configs_f1_0 = fun_test.parse_file_to_json(abstract_config_f1_0)
                file_contents = self.abstract_configs_f1_0
            if str(f1.split("-")[-1]) == "1":
                self.abstract_configs_f1_1 = fun_test.parse_file_to_json(abstract_config_f1_1)
                file_contents = self.abstract_configs_f1_1
            linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/abstract_cfg")
            linux_obj.command("rm %s" % file_name)
            linux_obj.create_file(file_name=file_name, contents=json.dumps(file_contents))
            linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/")
            fun_test.log("")
            fun_test.log("=======================")
            fun_test.log("Execute Abstract Config")
            fun_test.log("=======================")
            execute_abstract = linux_obj.command("./apply_abstract_config.py --server " + self.mpg_ips[f1] +
                                                 " --json ./abstract_cfg/" + file_name)
            fun_test.test_assert(expression="returned non-zero exit status" not in execute_abstract,
                                 message="Execute abstract config on %s" % f1)
        fun_test.sleep(message="Waiting for protocol coneverge", seconds=15)

        linux_obj.disconnect()

    def assign_mpg_ips(self, static=False, f1_1_mpg=None, f1_0_mpg=None, f1_0_mpg_netmask="255.255.255.0",
                       f1_1_mpg_netmask="255.255.255.0"):

        self._get_docker_names()
        linux_containers = {}

        for docker_name in self.docker_names:
            ip_check = False
            linux_containers[docker_name] = FunCpDockerContainer(name=docker_name.rstrip(),
                                                                 host_ip=self.fs_spec['come']['mgmt_ip'],
                                                                 ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                                                 ssh_password=self.fs_spec['come']['mgmt_ssh_password'])

            linux_containers[docker_name].command(command="sudo ifconfig mpg up", timeout=300)

            if not static:
                random_mac = [0x00, 0xf1, 0x1d, random.randint(0x00, 0x7f), random.randint(0x00, 0xff),
                              random.randint(0x00, 0xff)]
                mac = ':'.join(map(lambda x: "%02x" % x, random_mac))
                fun_test.test_assert(expression=mac, message="Generate Random MAC")

                try:
                    linux_containers[docker_name].command(command="sudo ifconfig mpg hw ether " + mac, timeout=60)

                except:
                    linux_containers[docker_name].command(command="ifconfig mpg")
                    op = linux_containers[docker_name].command(command="ifconfig mpg").split('\r\n')
                    for line in op:
                        ether = False
                        for word in line.split():
                            if "ether" == word:
                                ether = True
                                continue
                            if ether:
                                fun_test.test_assert_expected(expected=mac, actual=word,
                                                              message="Make sure MAC is updated "
                                                                      "on %s" % docker_name)
                                break
                linux_containers[docker_name].sudo_command(command="dhclient -v -i mpg", timeout=300)

            else:
                try:
                    if str(docker_name.split("-")[-1]).rstrip() == "0":
                        linux_containers[docker_name].command(command="sudo ifconfig mpg %s netmask %s" %
                                                                      (f1_0_mpg, f1_0_mpg_netmask), timeout=60)
                    elif str(docker_name.split("-")[-1]).rstrip() == "1":
                        linux_containers[docker_name].command(command="sudo ifconfig mpg %s netmask %s" %
                                                                      (f1_1_mpg, f1_1_mpg_netmask), timeout=60)
                except:
                    linux_containers[docker_name].command(command="ifconfig mpg")
                    ifconfig_output = linux_containers[docker_name].command(command="ifconfig mpg").split('\r\n')[1]
                    linux_containers[docker_name].command(command="ls")
                    mpg_ip = ifconfig_output.split()[1]
                    socket.inet_aton(mpg_ip)
                    fun_test.test_assert(expression=self.is_valid_ip(mpg_ip),
                                         message="Make sure MPG IP is assigned on %s" % docker_name)
                    self.mpg_ips[str(docker_name.rstrip())] = mpg_ip
                    ip_check = True
                if not ip_check:
                    ifconfig_output = linux_containers[docker_name].command(command="ifconfig mpg").split('\r\n')[1]
                    mpg_ip = ifconfig_output.split()[1]
                    socket.inet_aton(mpg_ip)
                    fun_test.test_assert(expression=self.is_valid_ip(mpg_ip),
                                         message="Make sure MPG IP is assigned on %s" % docker_name)
                    self.mpg_ips[str(docker_name.rstrip())] = mpg_ip
            linux_containers[docker_name].disconnect()
            fun_test.log(self.mpg_ips)

    def prepare_come_for_control_plane(self):
        linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                          ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                          ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        ws = "/mnt/keep"
        if not linux_obj.check_file_directory_exists(path=ws):
            linux_obj.create_directory(dir_name=ws, sudo=True)
        funsdk_obj = funcp.FunSDK(linux_obj, ws=ws)
        # sudo chmod -R ugo+rw /mnt
        fun_test.test_assert(funsdk_obj.clone(), 'git clone FunSDK repo')
        linux_obj.sudo_command(command="apt-get upgrade")
        linux_obj.sudo_command(command="apt-get install python build-essential gcc-8 libelf-dev python-parse "
                                       "python-yaml python-jinja2 python-pip")
        linux_obj.sudo_command(command="pip install pexpect")
        linux_obj.sudo_command(command="apt-get install docker.io")
        #add usermod
        linux_obj.disconnect()

    def funcp_sanity(self, check_bgp=False):

        linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                              ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                              ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        if check_bgp:
            #TODO do sanity check to verify BGP is working
            pass

    def fetch_mpg_ips(self):
        self.mpg_ips = {}
        self._get_docker_names()

        for docker_name in self.docker_names:
            linux_obj = FunCpDockerContainer(name=docker_name.rstrip(), host_ip=self.fs_spec['come']['mgmt_ip'],
                                             ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                             ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            linux_obj.command(command="ifconfig mpg")
            ifconfig_output = linux_obj.command(command="ifconfig mpg").split('\r\n')[1]
            linux_obj.command(command="ls")
            mpg_ip = ifconfig_output.split()[1]
            self.mpg_ips[str(docker_name.rstrip())] = mpg_ip
            linux_obj.disconnect()

    def add_routes_on_f1(self, routes_dict):
        self._get_docker_names()
        linux_obj = object
        for docker_name in self.docker_names:
            routes = routes_dict[docker_name.rstrip()]
            for num in routes:
                try:
                    linux_obj = FunCpDockerContainer(name=docker_name.rstrip(), host_ip=self.fs_spec['come']['mgmt_ip'],
                                                     ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                                     ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
                    fun_test.log("")
                    fun_test.log("======================")
                    fun_test.log("Add static route on %s" % docker_name)
                    fun_test.log("======================")
                    linux_obj.command(command="sudo ip route add %s via %s dev %s" % (routes[num]["route"],
                                                                                      routes[num]["gateway"],
                                                                                      routes[num]["port"]))
                    linux_obj.command(command="route -n")
                    linux_obj.disconnect()
                except:
                    linux_obj.disconnect()
                    linux_obj.command(command="docker exec -it " + docker_name.rstrip() + " bash", timeout=300)
                    op = linux_obj.command(command="route -n")
                    fun_test.log(op)
                    fun_test.test_assert(expression=routes[num]["route"][:-3] in op, message="Route Added")

            linux_obj.disconnect()

    def is_valid_ip(self, ip):
        m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

    def cleanup_funcp(self):
        fun_test.log("=====================")
        fun_test.log("Control Plane Cleanup")
        fun_test.log("=====================")
        self._get_docker_names(verify_2_dockers=False)
        self.docker_names_got = False
        linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                          ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                          ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        if not linux_obj.check_ssh():
            fun_test.critical("Cannot ssh into COMe, skipping FunCP Cleanup")
            return False
        funeth_op = linux_obj.command(command="lsmod | grep funeth")
        try:
            if "funeth" in funeth_op:
                funeth_rm = linux_obj.sudo_command("rmmod funeth")
                if "ERROR" not in funeth_rm:
                    fun_test.log("Funeth removed succesfully")
                else:
                    fun_test.critical(message="Funeth Remove error")

            for docker_name in self.docker_names:
                if not re.search('[a-zA-Z]', docker_name):
                    continue
                linux_obj.sudo_command(command="docker kill " + docker_name.rstrip(), timeout=300)
        except:
            fun_test.critical(message="Cannot cleanup FunCP")

    def _get_docker_names(self, verify_2_dockers=True):
        if self.docker_names_got:
            return
        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                               ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        docker_output = linux_obj_come.command(command="docker ps -a")
        print "\n" + docker_output
        self.docker_names = map(lambda s: s.strip(),
                                linux_obj_come.command(command="docker ps --format '{{.Names}}'").split("\r\n"))
        if verify_2_dockers:
            fun_test.test_assert_expected(expected=2, actual=len(self.docker_names),
                                          message="Make sure 2 dockers are up")
        self.docker_names_got = True
        linux_obj_come.disconnect()

    def test_cc_pings_fs(self, interval=1):
        self._get_docker_names()
        self._get_vlan1_ips()
        ping_success = False

        for host in self.docker_names:

            for docker in self.vlan1_ips:
                if host.rstrip() == docker.rstrip():
                    continue
                result = False
                percentage_loss = 100
                linux_obj = FunCpDockerContainer(name=host.rstrip(), host_ip=self.fs_spec['come']['mgmt_ip'],
                                                 ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                                 ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
                #fun_test.simple_assert((self.is_valid_ip(ip=self.vlan1_ips[host.rstrip()]) and
                #                       self.is_valid_ip(self.vlan1_ips[docker])), "Ensure valid vlan ip address")
                output = linux_obj.command("sudo ping -c 5 -i %s -I %s %s " % (interval,
                                                                               self.vlan1_ips[host.rstrip()],
                                                                               self.vlan1_ips[docker]))

                linux_obj.disconnect()
                m = re.search(r'(\d+)%\s+packet\s+loss', output)
                if m:
                    percentage_loss = int(m.group(1))
                if percentage_loss <= 50:
                    result = True
                if result:
                    ping_success = True
                    fun_test.log("=============================")
                    fun_test.add_checkpoint("Container %s can ping %s" % (host.rstrip(),
                                                                          self.vlan1_ips[host.rstrip()]))
                    fun_test.log("=============================")
                else:
                    ping_success = False
                    fun_test.log("=================================")
                    fun_test.critical(message="Container %s cannot ping %s" % (host.rstrip(),
                                                                               self.vlan1_ips[host.rstrip()]))
                    fun_test.log("=================================")
        return ping_success

    def test_cc_pings_remote_fs(self, dest_ips, docker_name=None, from_vlan=False, interval=1):
        if not docker_name:
            self._get_docker_names()
        self._get_vlan1_ips()
        ping_success = False
        docker_list = []
        if docker_name:
            docker_list.append(docker_name)
        else:
            docker_list = self.docker_names

        for host in docker_list:
            linux_obj = FunCpDockerContainer(name=host.rstrip(), host_ip=self.fs_spec['come']['mgmt_ip'],
                                             ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                             ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            for ips in dest_ips:
                result = False
                percentage_loss = 100
                #fun_test.simple_assert((self.is_valid_ip(self.vlan1_ips[host.rstrip()]) and self.is_valid_ip(ips)),
                #                       "Ensure valid vlan ip address")
                if from_vlan:
                    command = "sudo ping -c 5 -i %s -I %s  %s " % (interval, self.vlan1_ips[host.rstrip()], ips)
                else:
                    command = "sudo ping -c 5 -i %s %s " % (interval, ips)
                output = linux_obj.command(command, timeout=30)
                m = re.search(r'(\d+)%\s+packet\s+loss', output)
                if m:
                    percentage_loss = int(m.group(1))
                if percentage_loss <= 50:
                    result = True
                if result:
                    ping_success = True
                    fun_test.log("")
                    fun_test.log("=============================")
                    fun_test.log("Container %s can ping %s" % (host.rstrip(), ips))
                    fun_test.log("=============================")
                else:
                    ping_success = False
                    fun_test.critical(message="Container %s cannot ping %s" % (host.rstrip(), ips))
                    break
            linux_obj.disconnect()
        return ping_success

    def _get_vlan1_ips(self):
        if self.vlan_ips_got:
            return
        self.vlan1_ips = {}
        self._get_docker_names()

        for docker_name in self.docker_names:
            linux_obj = FunCpDockerContainer(name=docker_name.rstrip(), host_ip=self.fs_spec['come']['mgmt_ip'],
                                             ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                             ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            linux_obj.command(command="ifconfig vlan1")
            ifconfig_output = linux_obj.command(command="ifconfig vlan1").split('\r\n')[1]
            linux_obj.command(command="ls")
            vlan1_ip = ifconfig_output.split()[1]
            self.vlan1_ips[str(docker_name.rstrip())] = vlan1_ip
            self.vlan_ips_got = True
            linux_obj.disconnect()

    def check_come_stuck(self, fs_obj):

        linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                           ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                           ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        count = 1
        while True:
            count += 1
            response = os.system("ping -c 1 " + self.fs_spec['come']['mgmt_ip'])
            if count > 10:
                break
            if response == 0:
                if not linux_obj.check_ssh():
                    fs_obj.from_bmc_reset_come()
                    fun_test.sleep(message="Wating for COMe reset", seconds=120)
                    break
                else:
                    break
            else:
                "Cannot ping host"
                fun_test.sleep(seconds=10, message="waiting for host")

    def get_vlan_ips(self, come_dict, vlan_interface="vlan1"):
        vlan_list = []
        try:
            for come in come_dict:
                docker_obj = FunCpDockerContainer(name="F1-0", host_ip=come['come_ip'],
                                                  ssh_username=come['come_username'],
                                                  ssh_password=come['come_password'])

                contents = docker_obj.command('ifconfig %s' % vlan_interface)
                m = re.search(r'inet\s+(\d+.\d+.\d+.\d+)', contents.strip(), re.DOTALL)
                if m:
                    vlan_list.append(m.group(1))
        except Exception as ex:
            fun_test.critical(str(ex))
        return vlan_list

    def fetch_host_interface_ip(self, host_name, host_username, host_password):
        hu_ip = None
        try:
            linux_obj = Linux(host_ip=host_name, ssh_username=host_username, ssh_password=host_password)

            contents = linux_obj.command(command="ip address")
            m = re.search(r'hu\d+-f\d+.*.inet\s+(\d+.\d+.\d+.\d+)', contents.strip(), re.DOTALL)
            if m:
                hu_ip = m.group(1).strip()
        except Exception as ex:
            fun_test.critical(str(ex))
        return hu_ip

    def _ensure_route_exists(self, linux_obj, network, interface, gateway):
        result = False
        try:
            ip_route = linux_obj.get_ip_route()
            if network in ip_route:
                fun_test.test_assert_expected(expected=interface, actual=ip_route[network][gateway])
            else:
                linux_obj.ip_route_add(network=network, gateway=gateway, interface=interface)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_network_by_ip(self, ip, subnet=24):
        return '.'.join(ip.split('.')[:3]) + '.0' + '/%s' % subnet

    def _get_gateway_by_ip(self, ip):
        x = ip.split('.')
        x[3] = '1'
        return '.'.join(x)

    def get_hu_interface_on_host(self, linux_obj):
        interface_name = None
        try:
            contents = linux_obj.command(command="ip address")
            m = re.search(r'(hu\d+-f\d+)', contents.strip(), re.DOTALL)
            if m:
                interface_name = m.group(1).strip()
        except Exception as ex:
            fun_test.critical(str(ex))
        return interface_name

    def _ensure_same_network(self, network1, network2):
        return network1 == network2

    @staticmethod
    def get_list_of_hosts_connected_each_f1(topology_info):
        hosts = []
        try:
            for fs in topology_info['racks']:
                fs_f1_dict = {fs['name']: {}}
                for f1 in fs['F1s']:
                    fs_f1_dict[fs['name']].update({f1['id']: f1['Hosts']})
                hosts.append(fs_f1_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return hosts

    def get_rx_tx_ifconfig(self, interface_name, linux_obj):
        result = {"rx_packets": None, "tx_packets": None}
        try:
            cmd = "ifconfig %s | egrep \"RX packets | TX packets\" " % interface_name
            output = linux_obj.command(cmd)
            rx_packets = int(re.search(r'RX\s+packets\s+(\d+)', output).group(1))
            tx_packets = int(re.search(r'TX\s+packets\s+(\d+)', output).group(1))
            result["rx_packets"] = rx_packets
            result["tx_packets"] = tx_packets
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _test_intra_f1_ping(self, network_controller_obj, hosts):
        result = False
        try:
            count = 5000
            for host in hosts:
                linux_obj = Linux(host_ip=host['name'], ssh_username=host['ssh_username'],
                                  ssh_password=host['ssh_password'])
                for index in range(len(hosts)):
                    if host['ip'] == hosts[index]['ip']:
                        continue
                    checkpoint = "Ping from %s to %s" % (host['ip'], hosts[index]['ip'])
                    res = linux_obj.ping(dst=hosts[index]['ip'], count=2, interval=0.01, sudo=True)
                    fun_test.simple_assert(res, checkpoint)

                    erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)
                    vppkts_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
                    fcp_stats_before = network_controller_obj.peek_fcp_global_stats()
                    hu_interface = self.get_hu_interface_on_host(linux_obj=linux_obj)
                    ifconfig_stats_before = self.get_rx_tx_ifconfig(interface_name=hu_interface, linux_obj=linux_obj)

                    checkpoint = "hping from %s to %s" % (host['ip'], hosts[index]['ip'])
                    res = linux_obj.hping(dst=hosts[index]['ip'], count=count, mode='faster', protocol_mode='icmp',
                                          timeout=10)
                    # fun_test.simple_assert(res, checkpoint)
                    ifconfig_stats = self.get_rx_tx_ifconfig(interface_name=hu_interface, linux_obj=linux_obj)
                    diff_stats = get_diff_stats(old_stats=ifconfig_stats_before, new_stats=ifconfig_stats)
                    fun_test.log("Diff stats for Ifconfig %s interface: %s" % (hu_interface, diff_stats))
                    fun_test.simple_assert(
                        expression=(diff_stats['rx_packets'] >= count and diff_stats['tx_packets'] >= count),
                        message=checkpoint)

                    checkpoint = "Validate ERP stats"
                    erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
                    diff_stats = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats)
                    fun_test.log("ERP Diff stats: %s" % diff_stats)
                    fun_test.simple_assert(diff_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED] >= count, checkpoint)

                    checkpoint = "Validate vppkts stats"
                    vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
                    diff_stats = get_diff_stats(old_stats=vppkts_before, new_stats=vp_stats)
                    fun_test.log("VP packets Diff: %s" % diff_stats)
                    fun_test.test_assert_expected(expected=diff_stats[VP_FAE_REQUESTS_SENT],
                                                  actual=diff_stats[VP_FAE_RESPONSES_RECEIVED],
                                                  message="Ensure FAE req equal to sent ", ignore_on_success=True)
                    fun_test.log("VP HU OUT: %s and VP NU ETP OUT: %s" % (diff_stats[VP_PACKETS_OUT_HU],
                                                                          diff_stats[VP_PACKETS_OUT_NU_ETP]))
                    fun_test.simple_assert(expression=(diff_stats[VP_PACKETS_OUT_HU] >= count and
                                                       diff_stats[VP_PACKETS_OUT_NU_ETP] >= count), message=checkpoint)

                    #checkpoint = "Validate FCB stats"
                    #fcp_stats_after = network_controller_obj.peek_fcp_global_stats()
                    #diff_stats = get_diff_stats(new_stats=fcp_stats_after, old_stats=fcp_stats_before)
                    #fun_test.log("FCB Diff stats: %s" % diff_stats)
                    #fun_test.test_assert_expected(expected=0, actual=diff_stats[FCB_SRC_REQ_MSG_XMTD],
                    #                              message=checkpoint, ignore_on_success=True)
                    #fun_test.test_assert_expected(expected=0, actual=diff_stats[FCB_DST_REQ_MSG_RCVD],
                    #                              message=checkpoint, ignore_on_success=True)
                linux_obj.disconnect()
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_intra_f1_ping(self, dpc_info, hosts):
        result = False
        try:
            for fs in hosts:
                for fs_name in fs:
                    for f1 in fs[fs_name]:
                        checkpoint = "Test ping between hosts connected to F1_%s of %s" % (f1, fs_name)
                        fun_test.log_section(checkpoint)
                        dpc_server_ip = dpc_info[fs_name]['F1_%s_dpc' % f1][0]
                        dpc_server_port = dpc_info[fs_name]['F1_%s_dpc' % f1][1]
                        network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip,
                                                                   dpc_server_port=dpc_server_port)

                        res = self._test_intra_f1_ping(network_controller_obj=network_controller_obj,
                                                       hosts=fs[fs_name][f1])
                        fun_test.test_assert(res, checkpoint)
                        network_controller_obj.disconnect()
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_intra_fs_ping(self, hosts, dpc_info):
        result = False
        f1_0_dpc_obj = None
        f1_1_dpc_obj = None
        try:
            for fs in hosts:
                for fs_name in fs:
                    checkpoint = "Test ping from hosts connected to F1_0 of %s to F1_1 hosts of %s" % (fs_name,
                                                                                                       fs_name)
                    fun_test.log_section(checkpoint)
                    f1_0_hosts = fs[fs_name][0]
                    f1_1_hosts = fs[fs_name][1]
                    f1_0_dpc_obj = NetworkController(dpc_server_ip=dpc_info[fs_name]['F1_0_dpc'][0],
                                                     dpc_server_port=dpc_info[fs_name]['F1_0_dpc'][1])
                    f1_1_dpc_obj = NetworkController(dpc_server_ip=dpc_info[fs_name]['F1_1_dpc'][0],
                                                     dpc_server_port=dpc_info[fs_name]['F1_1_dpc'][1])
                    res = self._test_intra_fs_ping(f1_0_hosts=f1_0_hosts, f1_1_hosts=f1_1_hosts,
                                                   f1_0_dpc_obj=f1_0_dpc_obj, f1_1_dpc_obj=f1_1_dpc_obj)
                    fun_test.test_assert(res, checkpoint)
                    f1_1_dpc_obj.disconnect()
                    f1_0_dpc_obj.disconnect()
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        finally:
            if f1_1_dpc_obj and f1_0_dpc_obj:
                f1_1_dpc_obj.disconnect()
                f1_0_dpc_obj.disconnect()
        return result

    def validate_inter_rack_ping(self, fs_per_rack):
        result = False
        try:
            for fs in fs_per_rack:
                fs_name = fs['name']
                for _fs in fs_per_rack:
                    if fs['name'] == _fs['name']:
                        continue
                    checkpoint = "Test ping from source %s of one rack to dest %s of other rack" % (fs_name,
                                                                                                    _fs['name'])
                    result = self._test_ping_within_racks(remote_fs=_fs, local_fs=fs)
                    fun_test.test_assert(result, checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_intra_rack_ping(self, all_fs):
        result = False
        try:
            for fs in all_fs:
                fs_name = fs['name']
                for _fs in all_fs:
                    if fs['name'] == _fs['name']:
                        continue
                    checkpoint = "Test ping from source %s to dest %s of same rack" % (fs_name, _fs['name'])
                    result = self._test_ping_within_racks(remote_fs=_fs, local_fs=fs)
                    fun_test.test_assert(result, checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _fetch_spine_links(self, cx_links):
        spine_links = []
        for link in cx_links:
            spine_links.extend([int(re.search(r'(\d+)', k).group(1)) for k in link['interfaces'].keys()])
        return spine_links

    def _fetch_fabric_links(self, fab_links):
        fabric_links = []
        for key in fab_links:
            fabric_links.append(int(re.search(r'(\d+)', key).group(1)))
        return fabric_links

    def _test_ping_within_racks(self, remote_fs, local_fs, tolerance_in_percent=0.1):
        result = False
        try:
            count = 5000
            for f1 in local_fs['F1s']:
                spine_links = self._fetch_spine_links(cx_links=f1['CxLinks'])
                fab_links = self._fetch_fabric_links(fab_links=f1['FabLinks'])
                source_dpc_obj = NetworkController(dpc_server_ip=f1['F1_%s_dpc' % f1['id']][0],
                                                   dpc_server_port=f1['F1_%s_dpc' % f1['id']][1])
                f1_index = 0
                for host in f1['Hosts']:
                    linux_obj = Linux(host_ip=host['name'], ssh_username=host['ssh_username'],
                                      ssh_password=host['ssh_password'])
                    for remote_f1 in remote_fs['F1s']:
                        remote_spine_links = self._fetch_spine_links(cx_links=remote_f1['CxLinks'])
                        remote_fabric_links = self._fetch_fabric_links(fab_links=remote_f1['FabLinks'])
                        remote_dpc_obj = NetworkController(dpc_server_ip=remote_f1['F1_%s_dpc' % remote_f1['id']][0],
                                                           dpc_server_port=remote_f1['F1_%s_dpc' % remote_f1['id']][1])
                        for remote_host in remote_f1['Hosts']:
                            hu_interface_ip = remote_host['ip']
                            checkpoint = "Ping from %s to %s" % (host['ip'], hu_interface_ip)
                            res = linux_obj.ping(dst=hu_interface_ip, count=2, interval=0.01, sudo=True)
                            fun_test.simple_assert(res, checkpoint)

                            src_fcp_stats_before = source_dpc_obj.peek_fcp_global_stats()
                            remote_fcp_stats_before = remote_dpc_obj.peek_fcp_global_stats()
                            remote_vppkts_before = get_vp_pkts_stats_values(network_controller_obj=remote_dpc_obj)
                            src_vppkts_before = get_vp_pkts_stats_values(network_controller_obj=source_dpc_obj)
                            hu_interface = self.get_hu_interface_on_host(linux_obj=linux_obj)
                            ifconfig_stats_before = self.get_rx_tx_ifconfig(interface_name=hu_interface,
                                                                            linux_obj=linux_obj)
                            source_spine_links_bytes = {'before': {}, 'after': {}, 'diff': {}}
                            source_fabric_links_bytes = {'before': {}, 'after': {}, 'diff': {}}
                            remote_spine_links_bytes = {'before': {}, 'after': {}, 'diff': {}}
                            remote_fabric_links_bytes = {'before': {}, 'after': {}, 'diff': {}}
                            for fpg in spine_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=source_dpc_obj.peek_fpg_port_stats(port_num=fpg),
                                    stat_type=OCTETS_TRANSMITTED_OK)
                                source_spine_links_bytes['before'][fpg] = stats

                            for fpg in fab_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=source_dpc_obj.peek_fpg_port_stats(port_num=fpg),
                                    stat_type=OCTETS_TRANSMITTED_OK)
                                source_fabric_links_bytes['before'][fpg] = stats

                            for fpg in remote_spine_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=remote_dpc_obj.peek_fpg_port_stats(port_num=fpg),
                                    stat_type=OCTETS_RECEIVED_OK, tx=False)
                                remote_spine_links_bytes['before'][fpg] = stats

                            for fpg in remote_fabric_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=remote_dpc_obj.peek_fpg_port_stats(port_num=fpg),
                                    stat_type=OCTETS_RECEIVED_OK, tx=False)
                                remote_fabric_links_bytes['before'][fpg] = stats

                            checkpoint = "hping from %s to %s" % (host['ip'], hu_interface_ip)
                            res = linux_obj.hping(dst=hu_interface_ip, count=count, mode='faster', protocol_mode='icmp',
                                                  timeout=10)
                            # fun_test.simple_assert(res, checkpoint)
                            ifconfig_stats = self.get_rx_tx_ifconfig(interface_name=hu_interface, linux_obj=linux_obj)
                            diff_stats = get_diff_stats(old_stats=ifconfig_stats_before, new_stats=ifconfig_stats)
                            fun_test.log("Diff stats for Ifconfig %s interface: %s" % (hu_interface, diff_stats))
                            fun_test.simple_assert(
                                expression=(diff_stats['rx_packets'] >= count and diff_stats['tx_packets'] >= count),
                                message=checkpoint)

                            checkpoint = "Validate FCB stats"
                            src_fcp_stats = source_dpc_obj.peek_fcp_global_stats()
                            source_diff_stats = get_diff_stats(old_stats=src_fcp_stats_before, new_stats=src_fcp_stats)
                            remote_fcp_stats = remote_dpc_obj.peek_fcp_global_stats()
                            remote_diff_stats = get_diff_stats(old_stats=remote_fcp_stats_before,
                                                               new_stats=remote_fcp_stats)
                            fun_test.log("Source F1 FCP Diff stats: %s" % source_diff_stats)
                            fun_test.log("Remote F1 FCP Diff stats: %s" % remote_diff_stats)

                            fun_test.simple_assert(self.validate_fcp_stats_remote_local_f1(
                                src_diff_stats=source_diff_stats, remote_diff_stats=remote_diff_stats,
                                tolerance_in_percent=0.1), checkpoint)

                            checkpoint = "Validate Source F1 vppkts stats"
                            src_vp_stats = get_vp_pkts_stats_values(network_controller_obj=source_dpc_obj)
                            diff_stats = get_diff_stats(old_stats=src_vppkts_before, new_stats=src_vp_stats)
                            fun_test.log("Source F1 VP packets Diff: %s" % diff_stats)
                            fun_test.test_assert_expected(expected=diff_stats[VP_FAE_REQUESTS_SENT],
                                                          actual=diff_stats[VP_FAE_RESPONSES_RECEIVED],
                                                          message="Ensure FAE req equal to sent ",
                                                          ignore_on_success=True)
                            fun_test.log("VP HU OUT: %s and VP NU ETP OUT: %s" % (diff_stats[VP_PACKETS_OUT_HU],
                                                                                  diff_stats[VP_PACKETS_OUT_NU_ETP]))
                            fun_test.simple_assert(expression=(diff_stats[VP_PACKETS_OUT_HU] >= count and
                                                               diff_stats[VP_PACKETS_OUT_NU_ETP] >= count),
                                                   message=checkpoint)
                            checkpoint = "Validate Source F1 FPG spine and fabric links stats with tolerance of %s " \
                                         "percent" % tolerance_in_percent
                            for spine in spine_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=source_dpc_obj.peek_fpg_port_stats(port_num=spine),
                                    stat_type=OCTETS_TRANSMITTED_OK)
                                source_spine_links_bytes['after'][spine] = stats
                                source_spine_links_bytes['diff'][spine] = stats - source_spine_links_bytes['before'][
                                    spine]
                            for fabric in fab_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=source_dpc_obj.peek_fpg_port_stats(port_num=fabric),
                                    stat_type=OCTETS_TRANSMITTED_OK)
                                source_fabric_links_bytes['after'][fabric] = stats
                                source_fabric_links_bytes['diff'][fabric] = stats - source_fabric_links_bytes['before'][
                                    fabric]
                            fun_test.simple_assert(self.validate_spine_fabric_fpg_stats(
                                spine_stats=source_spine_links_bytes, fabric_stats=source_fabric_links_bytes,
                                tolerance_in_percent=5.0), checkpoint)

                            checkpoint = " Validate Remote F1 FPG spine and fabric links stats with tolerance of %s " \
                                         "percent" % tolerance_in_percent
                            for spine in remote_spine_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=remote_dpc_obj.peek_fpg_port_stats(port_num=spine),
                                    stat_type=OCTETS_RECEIVED_OK, tx=False)
                                remote_spine_links_bytes['after'][spine] = stats
                                remote_spine_links_bytes['diff'][spine] = stats - remote_spine_links_bytes['before'][
                                    spine]
                            for fab in remote_fabric_links:
                                stats = get_dut_output_stats_value(
                                    result_stats=remote_dpc_obj.peek_fpg_port_stats(port_num=fab),
                                    stat_type=OCTETS_RECEIVED_OK, tx=False)
                                remote_fabric_links_bytes['after'][fab] = stats
                                remote_fabric_links_bytes['diff'][fab] = stats - remote_fabric_links_bytes['before'][
                                    fab]
                            fun_test.simple_assert(self.validate_spine_fabric_fpg_stats(
                                spine_stats=remote_spine_links_bytes, fabric_stats=remote_fabric_links_bytes,
                                tolerance_in_percent=5.0), checkpoint)

                            checkpoint = "Validate Source F1 vppkts stats"
                            src_vp_stats = get_vp_pkts_stats_values(network_controller_obj=source_dpc_obj)
                            diff_stats = get_diff_stats(old_stats=remote_vppkts_before, new_stats=src_vp_stats)
                            fun_test.log("Source F1 VP packets Diff: %s" % diff_stats)
                            fun_test.test_assert_expected(expected=diff_stats[VP_FAE_REQUESTS_SENT],
                                                          actual=diff_stats[VP_FAE_RESPONSES_RECEIVED],
                                                          message="Ensure FAE req equal to sent ",
                                                          ignore_on_success=True)
                            fun_test.log("VP HU OUT: %s and VP NU ETP OUT: %s" % (diff_stats[VP_PACKETS_OUT_HU],
                                                                                  diff_stats[VP_PACKETS_OUT_NU_ETP]))
                            fun_test.simple_assert(expression=(diff_stats[VP_PACKETS_OUT_HU] >= count and
                                                               diff_stats[VP_PACKETS_OUT_NU_ETP] >= count),
                                                   message=checkpoint)

                    linux_obj.disconnect()
                    source_dpc_obj.disconnect()
                    remote_dpc_obj.disconnect()
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _test_intra_fs_ping(self, f1_0_hosts, f1_1_hosts, f1_0_dpc_obj, f1_1_dpc_obj):
        result = False
        try:
            count = 5000
            for f1_0_host in f1_0_hosts:
                linux_obj = Linux(host_ip=f1_0_host['name'], ssh_username=f1_0_host['ssh_username'],
                                  ssh_password=f1_0_host['ssh_password'])
                for f1_1_host in f1_1_hosts:
                    hu_interface_ip = f1_1_host['ip']
                    checkpoint = "Ping from %s to %s" % (f1_0_host['ip'], hu_interface_ip)
                    res = linux_obj.ping(dst=hu_interface_ip, count=2, interval=0.01, sudo=True)
                    fun_test.simple_assert(res, checkpoint)

                    fcp_stats_before = f1_0_dpc_obj.peek_fcp_global_stats()
                    vppkts_before = get_vp_pkts_stats_values(network_controller_obj=f1_0_dpc_obj)
                    hu_interface = self.get_hu_interface_on_host(linux_obj=linux_obj)
                    ifconfig_stats_before = self.get_rx_tx_ifconfig(interface_name=hu_interface, linux_obj=linux_obj)

                    checkpoint = "hping from %s to %s" % (f1_0_host['ip'], hu_interface_ip)
                    res = linux_obj.hping(dst=hu_interface_ip, count=count, mode='faster', protocol_mode='icmp',
                                          timeout=10)
                    # fun_test.simple_assert(res, checkpoint)
                    ifconfig_stats = self.get_rx_tx_ifconfig(interface_name=hu_interface, linux_obj=linux_obj)
                    diff_stats = get_diff_stats(old_stats=ifconfig_stats_before, new_stats=ifconfig_stats)
                    fun_test.log("Diff stats for Ifconfig %s interface: %s" % (hu_interface, diff_stats))
                    fun_test.simple_assert(
                        expression=(diff_stats['rx_packets'] >= count and diff_stats['tx_packets'] >= count),
                        message=checkpoint)

                    checkpoint = "Validate FCB stats"
                    fcp_stats = f1_0_dpc_obj.peek_fcp_global_stats()
                    diff_stats = get_diff_stats(old_stats=fcp_stats_before, new_stats=fcp_stats)
                    fun_test.log("FCP Diff stats: %s" % diff_stats)
                    '''
                    fun_test.simple_assert(
                        expression=(int(diff_stats[FCB_TDP0_DATA]) + int(diff_stats[FCB_TDP0_GNT]) +
                                    int(diff_stats[FCB_TDP0_REQ])) >= count, message="Ensure TDP0 packets")
                    fun_test.simple_assert(
                        expression=(int(diff_stats[FCB_TDP1_DATA]) + int(diff_stats[FCB_TDP1_GNT]) +
                                    int(diff_stats[FCB_TDP1_REQ])) >= count, message="Ensure TDP1 packets")
                    fun_test.simple_assert(
                        expression=(int(diff_stats[FCB_TDP2_DATA]) + int(diff_stats[FCB_TDP2_GNT]) +
                                    int(diff_stats[FCB_TDP2_REQ])) >= count, message="Ensure TDP2 packets")
                    fun_test.add_checkpoint(checkpoint)
                    '''
                    fun_test.simple_assert(
                        expression=(int(diff_stats[FCB_DST_FCP_PKT_RCVD]) >= count and
                                    int(diff_stats[FCB_DST_REQ_MSG_RCVD]) >= count and
                                    int(diff_stats[FCB_SRC_GNT_MSG_RCVD]) >= count and
                                    int(diff_stats[FCB_SRC_REQ_MSG_XMTD]) >= count), message=checkpoint)

                    checkpoint = "Validate vppkts stats"
                    vp_stats = get_vp_pkts_stats_values(network_controller_obj=f1_0_dpc_obj)
                    diff_stats = get_diff_stats(old_stats=vppkts_before, new_stats=vp_stats)
                    fun_test.log("VP packets Diff: %s" % diff_stats)
                    fun_test.test_assert_expected(expected=diff_stats[VP_FAE_REQUESTS_SENT],
                                                  actual=diff_stats[VP_FAE_RESPONSES_RECEIVED],
                                                  message="Ensure FAE req equal to sent ", ignore_on_success=True)
                    fun_test.log("VP HU OUT: %s and VP NU ETP OUT: %s" % (diff_stats[VP_PACKETS_OUT_HU],
                                                                          diff_stats[VP_PACKETS_OUT_NU_ETP]))
                    fun_test.simple_assert(expression=(diff_stats[VP_PACKETS_OUT_HU] >= count and
                                                       diff_stats[VP_PACKETS_OUT_NU_ETP] >= count), message=checkpoint)
                linux_obj.disconnect()
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_spine_fabric_fpg_stats(self, spine_stats, fabric_stats, tolerance_in_percent):
        result = False
        try:
            checkpoint = "Ensure spine links byte count is equal with tolerance of %s percent" % tolerance_in_percent
            for count1, count2 in itertools.combinations(spine_stats['diff'].values(), 2):
                fun_test.simple_assert(self.test_assert_with_tolerance(
                    expected=count1, actual=count2, tolerance_in_percent=tolerance_in_percent), checkpoint)

            checkpoint = "Ensure fabric link byte count should be equal to spine link byte count * no_of_spine_links " \
                         "with tolerance of %s percent" % tolerance_in_percent
            expected_fabric_link_count = spine_stats['diff'].values()[0] * len(spine_stats['diff'].values())
            fun_test.log('Expected Fabric Link bytes: %d' % expected_fabric_link_count)
            for fabric, byte_count in fabric_stats['diff'].items():
                fun_test.simple_assert(self.test_assert_with_tolerance(
                    expected=expected_fabric_link_count, actual=byte_count, tolerance_in_percent=tolerance_in_percent),
                    checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def test_assert_with_tolerance(self, expected, actual, tolerance_in_percent=0.1):
        result = False
        try:
            if int(expected) == int(actual):
                result = True
            else:
                delta = expected * float(tolerance_in_percent)
                lower_limit = expected - delta
                upper_limit = expected + delta

                fun_test.simple_assert(expression=(lower_limit <= actual <= upper_limit),
                                       message="Assert with tolerance failed Expected: %s Actual: %s Delta: %s "
                                               "Tolerance: %s percent" % (expected, actual, delta,
                                                                          tolerance_in_percent))
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_fcp_stats_remote_local_f1(self, src_diff_stats, remote_diff_stats, tolerance_in_percent=0.1):
        result = False
        try:
            checkpoint = "Ensure total FCP request sent from source F1 == total FCP request received on remote F1 with " \
                         "tolerance of %d percent " % tolerance_in_percent
            total_req_sent = src_diff_stats['tdp0_req'] + src_diff_stats['tdp1_req'] + src_diff_stats['tdp2_req']
            total_req_recv = remote_diff_stats['tdp0_req'] + remote_diff_stats['tdp1_req'] + remote_diff_stats['tdp2_req']
            fun_test.log("Total FCP Request Sent: %s Total FCP Request Received: %s" % (total_req_sent, total_req_recv))
            fun_test.simple_assert(self.test_assert_with_tolerance(expected=total_req_sent, actual=total_req_recv,
                                                                   tolerance_in_percent=tolerance_in_percent),
                                   checkpoint)

            checkpoint = "Ensure total FCP grant received on source F1 == total FCP grant sent from remote F1 with " \
                         "tolerance of %d percent " % tolerance_in_percent
            total_gnt_recv = src_diff_stats['tdp0_gnt'] + src_diff_stats['tdp1_gnt'] + src_diff_stats['tdp2_gnt']
            total_gnt_sent = remote_diff_stats['tdp0_gnt'] + remote_diff_stats['tdp1_gnt'] + remote_diff_stats['tdp2_gnt']
            fun_test.log("Total FCP Grant Sent: %s Total FCP Grant Received: %s" % (total_gnt_sent, total_gnt_recv))
            fun_test.simple_assert(self.test_assert_with_tolerance(expected=total_gnt_sent, actual=total_gnt_recv,
                                                                   tolerance_in_percent=tolerance_in_percent),
                                   checkpoint)

            checkpoint = "Ensure total FCP data sent from source F1 == total FCP data received on remote F1 with " \
                         "tolerance of %d percent " % tolerance_in_percent
            total_data_sent = src_diff_stats['tdp0_data'] + src_diff_stats['tdp1_data'] + src_diff_stats['tdp2_data']
            total_data_recv = remote_diff_stats['tdp0_data'] + remote_diff_stats['tdp1_data'] + remote_diff_stats[
                'tdp2_data']
            fun_test.log("Total FCP Data Sent: %s Total FCP Data Received: %s" % (total_data_sent, total_data_recv))
            fun_test.simple_assert(self.test_assert_with_tolerance(expected=total_data_sent, actual=total_data_recv,
                                                                   tolerance_in_percent=tolerance_in_percent),
                                   checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    @staticmethod
    def get_dpc_ip_port_for_each_f1(topology_info):
        info = {}
        try:
            for fs in topology_info['racks']:
                dpc_info = {fs['name']: {}}
                for f1 in fs['F1s']:
                    key = "F1_%s_dpc" % f1['id']
                    val = tuple(f1[key])
                    dpc_info[fs['name']].update({key: val})
                info.update(dpc_info)
        except Exception as ex:
            fun_test.critical(str(ex))
        return info

    @staticmethod
    def get_list_of_all_hosts(topology_info):
        hosts = []
        try:
            hosts = []
            for fs in topology_info['racks']:
                for f1 in fs['F1s']:
                    hosts.extend(f1['Hosts'])
        except Exception as ex:
            fun_test.critical(str(ex))
        return hosts

    @staticmethod
    def get_list_of_fs_per_rack(topology_info):
        fs_per_rack = []
        try:
            for index in range(topology_info['no_of_racks']):
                fs_per_rack.append(topology_info['racks'][index])
        except Exception as ex:
            fun_test.critical(str(ex))
        return fs_per_rack








