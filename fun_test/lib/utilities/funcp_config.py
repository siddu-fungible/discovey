from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import json
import random
from scripts.networking.lib_nw import funcp


class FunControlPlaneBringup:

    def __init__(self, fs_name, boot_image_f1_0="funos-f1.stripped_retimer_test_vdd_delay.gz",
                 boot_image_f1_1="funos-f1.stripped_retimer_test_vdd_delay.gz", boot_args_f1_0=None,
                 boot_args_f1_1=None):
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

    def boot_both_f1(self, power_cycle_come=True, reboot_come=True):
        fs_0 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_0,
                      boot_args=self.boot_args_f1_0)
        fs_1 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_1,
                      boot_args=self.boot_args_f1_1)
        fun_test.simple_assert(fs_0, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs_0.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs_0.set_f1s(), "Set F1s")
        fun_test.test_assert(fs_0.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs_0.bmc.u_boot_load_image(index=0, tftp_image_path=fs_0.tftp_image_path,
                                                        boot_args=fs_0.boot_args),
                             "U-Bootup f1: {} complete".format(0))
        fs_0.bmc.start_uart_log_listener(f1_index=0)
        fun_test.test_assert(
            fs_0.bmc.u_boot_load_image(index=1, tftp_image_path=fs_1.tftp_image_path, boot_args=fs_1.boot_args),
            "U-Bootup f1: {} complete".format(1))
        fs_0.bmc.start_uart_log_listener(f1_index=1)
        if reboot_come:
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
        return True

    def boot_f1_0(self, power_cycle_come=True):
        fs_0 = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_0,
                      boot_args=self.boot_args_f1_0, disable_f1_index=1)

        fun_test.simple_assert(fs_0, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs_0.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs_0.set_f1s(), "Set F1s")
        fun_test.test_assert(fs_0.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs_0.bmc.u_boot_load_image(index=0, tftp_image_path=fs_0.tftp_image_path,
                                                        boot_args=fs_0.boot_args),
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

    def boot_f1_1(self, power_cycle_come=True):
        fs = Fs.get(fs_spec=self.fs_spec, tftp_image_path=self.boot_image_f1_1,
                      boot_args=self.boot_args_f1_1, disable_f1_index=0)

        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs.set_f1s(), "Set F1s")
        fun_test.test_assert(fs.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs.bmc.u_boot_load_image(index=1, tftp_image_path=fs.tftp_image_path,
                                                        boot_args=fs.boot_args),
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

    def bringup_funcp(self, prepare_docker=True):
        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                               ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        ssh_test_come = linux_obj_come.check_ssh()
        fun_test.test_assert(expression=ssh_test_come, message="Make sure ssh can be done to COMe")
        come_lspci = linux_obj_come.lspci(grep_filter="1dad:")
        if prepare_docker:

            linux_obj_come.command(command="cd /mnt/keep/FunSDK/")
            git_pull = linux_obj_come.command("git pull")

            prepare_docker_output = linux_obj_come.command("./integration_test/emulation/test_system.py --prepare "
                                                           "--docker", timeout=1200)
            sections = ['Cloning into \'FunSDK\'', 'Cloning into \'fungible-host-drivers\'',
                        'Cloning into \'FunControlPlane\'', 'Prepare End']
            for section in sections:
                fun_test.test_assert(section in prepare_docker_output, "{} seen".format(section))
        linux_obj_come.command(command="cd /mnt/keep/FunSDK/")

        setup_docker_output = linux_obj_come.command("./integration_test/emulation/test_system.py --setup --docker",
                                                     timeout=1200)
        sections = ['Bring up Control Plane', 'Device 1dad:', 'move fpg interface to f0 docker',
                    'libfunq bind  End', 'move fpg interface to f1 docker', 'Bring up Control Plane dockers']
        for section in sections:
            fun_test.test_assert(section in setup_docker_output, "{} seen".format(section))

        linux_obj_come.disconnect()
        return True

    def funcp_abstract_config(self, abstract_config_f1_0, abstract_config_f1_1, host_ip=None, workspace="/tmp",
                              ssh_username=None, ssh_password=None):
        if host_ip and ssh_password and ssh_username:
            linux_obj = Linux(host_ip=host_ip, ssh_username= ssh_username, ssh_password=ssh_password)
        else:
            linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                              ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                              ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
        funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)
        fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
        fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
        # Get FunControlPlane
        if abstract_config_f1_0:
            self.abstract_configs_f1_0 = fun_test.parse_file_to_json(abstract_config_f1_0)

        if abstract_config_f1_1:
            self.abstract_configs_f1_1 = fun_test.parse_file_to_json(abstract_config_f1_1)

        for f1 in self.mpg_ips:
            file_name = f1 + "_abstract.json"
            file_contents = None
            if f1 == "F1-0":
                file_contents = self.abstract_configs_f1_0
            if f1 == "F1-1":
                file_contents = self.abstract_configs_f1_1
            linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/abstract_cfg")
            linux_obj.create_file(file_name=file_name, contents=json.dumps(file_contents))
            linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/")
            fun_test.test_assert(expression=linux_obj.command("./apply_abstract_config.py --server " + self.mpg_ips[f1]
                                                              + " --json ./abstract_cfg/" + file_name),
                                 message="Execute abstract config on %s" % f1)
        linux_obj.disconnect()

    def assign_mpg_ips_dhcp(self):

        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                                    ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        docker_output = linux_obj_come.command(command="docker ps -a")
        print "\n" + docker_output
        self.docker_names = linux_obj_come.command(command="docker ps --format '{{.Names}}'").split("\r\n")
        fun_test.test_assert_expected(expected=2, actual=len(self.docker_names), message="Make sure 2 dockers are up")
        linux_obj_come.disconnect()
        linux_containers = {}

        for docker_name in self.docker_names:
            linux_containers[docker_name] = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                                                  ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                                                  ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            linux_containers[docker_name].command(command="docker exec -it " + docker_name.rstrip() + " bash",
                                                  timeout=300)

            linux_containers[docker_name].sudo_command(command="ifconfig mpg up", timeout=300)
            random_mac = [0x00, 0xf1, 0x1d, random.randint(0x00, 0x7f), random.randint(0x00, 0xff),
                          random.randint(0x00, 0xff)]
            mac = ':'.join(map(lambda x: "%02x" % x, random_mac))
            fun_test.test_assert(expression=mac, message="Generate Random MAC")

            try:
                linux_containers[docker_name].sudo_command(command="ifconfig mpg hw ether "+mac, timeout=60)

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
                            fun_test.test_assert_expected(expected=mac, actual=word, message="Make sure MAC is updated "
                                                                                             "on %s" % docker_name)
                            break

            linux_containers[docker_name].sudo_command(command="dhclient -v -i mpg", timeout=300)
            linux_containers[docker_name].command(command="ifconfig mpg")
            ifconfig_output = linux_containers[docker_name].command(command="ifconfig mpg").split('\r\n')[1]
            linux_containers[docker_name].command(command="ls")
            mpg_ip = ifconfig_output.split()[1]
            fun_test.test_assert(expression=mpg_ip, message="Make sure MPG IP is got through DHCP on %s" % docker_name)
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
        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                               ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        docker_output = linux_obj_come.command(command="docker ps -a")
        print "\n" + docker_output
        self.docker_names = linux_obj_come.command(command="docker ps --format '{{.Names}}'").split("\r\n")
        fun_test.test_assert_expected(expected=2, actual=len(self.docker_names), message="Make sure 2 dockers are up")
        linux_obj_come.disconnect()

        for docker_name in self.docker_names:
            linux_obj = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                              ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                              ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
            linux_obj.command(command="docker exec -it " + docker_name.rstrip() + " bash", timeout=300)
            linux_obj.command(command="ifconfig mpg")
            ifconfig_output = linux_obj.command(command="ifconfig mpg").split('\r\n')[1]
            linux_obj.command(command="ls")
            mpg_ip = ifconfig_output.split()[1]
            self.mpg_ips[str(docker_name.rstrip())] = mpg_ip
            linux_obj.disconnect()
