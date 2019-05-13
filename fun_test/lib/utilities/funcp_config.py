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

    def __init__(self, fs_name, boot_image_f1_0, boot_image_f1_1, boot_args_f1_0=None, boot_args_f1_1=None):
        self.fs_name = fs_name
        self.boot_image_f1_0 = boot_image_f1_0
        self.boot_image_f1_1 = boot_image_f1_1
        self.boot_args_f1_0 = boot_args_f1_0
        self.boot_args_f1_1 = boot_args_f1_1
        if not boot_args_f1_0:
            self.boot_args_f1_0 = "app=hw_hsu_test cc_huid=3 sku=SKU_FS1600_0 --all_100g --dis-stats --dpc-server " \
                                  "--dpc-uart --mgmt --serdesinit"
        if not boot_args_f1_1:
            self.boot_args_f1_1 = "app=hw_hsu_test cc_huid=2 sku=SKU_FS1600_1 --all_100g --dis-stats --dpc-server " \
                                  "--dpc-uart --mgmt  --serdesinit"
        self.fs_spec = fun_test.get_asset_manager().get_fs_by_name(fs_name)
        self.fs_boot_number = None
        self.abstract_configs = None
        self.mpg_ips = {}
        self.docker_names = []

    def boot_both_f1(self, power_cycle_come=True):
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
        fun_test.test_assert(fs_0.come_reset(power_cycle=True, non_blocking=True),
                             "ComE rebooted successfully")
        fun_test.sleep(message="waiting for COMe", seconds=120)
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

    def bringup_funcp(self):
        linux_obj_come = Linux(host_ip=self.fs_spec['come']['mgmt_ip'],
                               ssh_username=self.fs_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.fs_spec['come']['mgmt_ssh_password'])
        ssh_test_come = linux_obj_come.check_ssh()
        if not ssh_test_come:
            fun_test.test_assert(fs.from_bmc_reset_come(), "BMC Reset COMe")
            ssh_test_count = 0
            while True:
                fun_test.sleep(message="Power cycling COMe", seconds=120)
                if (ssh_test_count > 1) or ssh_test_come:
                    fun_test.test_assert_expected(expected=ssh_test_come, actual=True, message="")
                    break
                ssh_test_count += 1
        come_lspci = linux_obj_come.lspci(grep_filter="1dad:")
        linux_obj_come.command(command="cd /mnt/keep/FunSDK/")
        git_pull = linux_obj_come.command("git pull")
        prepare_docker_outout = linux_obj_come.command("./integration_test/emulation/test_system.py --prepare --docker",
                                                       timeout=1200)
        sections = ['Cloning into \'FunSDK\'', 'Cloning into \'fungible-host-drivers\'',
                    'Cloning into \'FunControlPlane\'', 'Prepare End']
        for section in sections:
            fun_test.test_assert(section in prepare_docker_outout, "{} seen".format(section))

        setup_docker_outout = linux_obj_come.command("./integration_test/emulation/test_system.py --setup --docker",
                                                     timeout=900)
        sections = ['Bring up Control Plane', 'Device 1dad:', 'move fpg interface to f0 docker',
                    'libfunq bind  End', 'move fpg interface to f1 docker', 'Bring up Control Plane dockers']
        for section in sections:
            fun_test.test_assert(section in setup_docker_outout, "{} seen".format(section))

    def funcp_abstract_config(self, abstract_config_file=None, workspace="/tmp",host_ip="qa-ubuntu-02",
                              ssh_username="qa-admin", ssh_password="Precious1*"):
        if not abstract_config_file:
            abstract_config_file = fun_test.get_script_parent_directory() + '/abstract_configs.json'
        self.abstract_configs = fun_test.parse_file_to_json(abstract_config_file)

        linux_obj = Linux(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
        funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)

        # Get FunControlPlane
        fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
        fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
        linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/abstract_cfg")
        for f1 in self.mpg_ips:
            file_name = f1 + "_abstract.json"
            file_contents = self.abstract_configs[f1]
            linux_obj.create_file(file_name=file_name, contents=json.dumps(file_contents))
            linux_obj.command("cd " + workspace + "/FunControlPlane/scripts/docker/combined_cfg/")
            fun_test.test_assert(expression=linux_obj.command("./apply_abstract_config.py --server " + mpg_ips[f1] +
                                                              " --json ./abstract_cfg/" + file_name),
                                 message="Execute abstract config on %s" % f1)

    def assign_mpg_ips(self):

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
            self.mpg_ips[str(docker_name.rstrip)] = mpg_ip
            linux_containers[docker_name].disconnect()
            fun_test.log(self.mpg_ips)
