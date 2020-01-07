from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import json
import random
from scripts.networking.lib_nw import funcp

test_bed_name = ""
fs = None
mpg_ips={}

class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure FS system is selected")

    def setup(self):
        global test_bed_name

        if fun_test.get_job_environment_variable('test_bed_type'):
            test_bed_name = fun_test.get_job_environment_variable('test_bed_type')
        else:
            test_bed_name = "fs-48"

    def cleanup(self):
        pass


class BootFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary=" Boot both F1s on FS",
                              steps="""
                              1. Get FS system : %s credentials, image and bootargs
                              2. Boot up FS system
                              """ % test_bed_name)

    def setup(self):
        pass

    def run(self):
        global fs
        test_bed_spec = fun_test.get_asset_manager().get_fs_spec(test_bed_name)
        img_path = "divya_funos-f1.stripped_june4.gz"
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0,1,2 --mgmt syslog=6 --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt syslog=6 --disable-wu-watchdog"
        fs = Fs.get(fs_spec=test_bed_spec, tftp_image_path=img_path,
                    boot_args=f1_0_boot_args)
        fs_1 = Fs.get(fs_spec=test_bed_spec, tftp_image_path=img_path,
                      boot_args=f1_1_boot_args)
        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(fs.set_f1s(), "Set F1s")
        fun_test.test_assert(fs.fpga_initialize(), "FPGA initiaize")
        fun_test.test_assert(fs.bmc.u_boot_load_image(index=0, tftp_image_path=fs.tftp_image_path,
                                                      boot_args=fs.boot_args, gateway_ip="10.1.105.1"),
                             "U-Bootup f1: {} complete".format(0))
        fs.bmc.start_uart_log_listener(f1_index=0, serial_device="")
        fun_test.test_assert(
            fs.bmc.u_boot_load_image(index=1, tftp_image_path=fs_1.tftp_image_path, boot_args=fs_1.boot_args, gateway_ip="10.1.105.1"),
            "U-Bootup f1: {} complete".format(1))
        fs.bmc.start_uart_log_listener(f1_index=1)
        fun_test.test_assert(fs.come_reset(power_cycle=True, non_blocking=True),
                             "ComE rebooted successfully")
        fun_test.sleep(message="waiting for COMe", seconds=120)
        come_ping_test = False

        come_ping_test_count = 0
        while not come_ping_test:
            response = os.system("ping -c 1 " + test_bed_spec['come']['mgmt_ip'])
            if response == 0:
                come_ping_test = True
            else:
                fun_test.sleep(message="Waiting for COMe to be pingable", seconds=15)
                come_ping_test_count+=0
                if come_ping_test_count >10:
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


    def cleanup(self):
        pass


class BringupFunCP(FunTestCase):

    test_bed_spec=None
    Come_reach = False

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup FunCP on COMe",
                              steps="""
                              1. Prepare Dockers
                              2. Bringup Dockers
                              """)

    def setup(self):
        self.test_bed_spec = fun_test.get_asset_manager().get_fs_spec(test_bed_name)

        linux_obj_come = None

        count = 0
        while not self.Come_reach:
            count += 1
            response = os.system("ping -c 1 " + self.test_bed_spec['come']['mgmt_ip'])
            if response == 0:
                self.Come_reach = True
            else:
                fun_test.sleep(message="Waiting for Come to be pingable", seconds=30)
                if count == 5:
                    break
        fun_test.test_assert(expression=self.Come_reach, message="Reach COMe")

    def run(self):

        linux_obj_come = Linux(host_ip=self.test_bed_spec['come']['mgmt_ip'],
                               ssh_username=self.test_bed_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.test_bed_spec['come']['mgmt_ssh_password'])
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

    def cleanup(self):
        pass


class ConfigureFunCPMpgIP(FunTestCase):
    test_bed_spec = None
    linux_obj_come = None
    docker_names = []
    def describe(self):
        self.set_test_details(id=3,
                              summary="Bringup MPG interface and assign IPs",
                              steps="""
                              1. Bring MPG up
                              2. Add new MAC
                              3. Get IP using DHCP
                              """)

    def setup(self):
        self.test_bed_spec = fun_test.get_asset_manager().get_fs_spec(test_bed_name)
        self.linux_obj_come = Linux(host_ip=self.test_bed_spec['come']['mgmt_ip'],
                               ssh_username=self.test_bed_spec['come']['mgmt_ssh_username'],
                               ssh_password=self.test_bed_spec['come']['mgmt_ssh_password'])
        docker_output = self.linux_obj_come.command(command="docker ps -a")
        print "\n"+docker_output
        self.docker_names = self.linux_obj_come.command(command="docker ps --format '{{.Names}}'").split("\r\n")
        fun_test.test_assert_expected(expected=2, actual=len(self.docker_names), message="Make sure 2 dockers are up")
        self.linux_obj_come.disconnect()
    def run(self):

        linux_containers = {}
        for docker_name in self.docker_names:
            linux_containers[docker_name] = Linux(host_ip=self.test_bed_spec['come']['mgmt_ip'],
                                                  ssh_username=self.test_bed_spec['come']['mgmt_ssh_username'],
                                                  ssh_password=self.test_bed_spec['come']['mgmt_ssh_password'])
            linux_containers[docker_name].command(command="docker exec -it "+docker_name.rstrip()+" bash", timeout=300)

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
            mpg_ips[str(docker_name.rstrip)] = mpg_ip
            linux_containers[docker_name].disconnect()

        fun_test.log(mpg_ips)
        # self.linux_obj_come.command(command="cd /workspace/FunControlPlane/scripts/docker/combined_cfg/")
        # self.linux_obj_come.command(command="ls")
        # result = self.linux_obj_come.command(command="sudo ifconfig fpg1 up", timeout=300)
        # result = self.linux_obj_come.command(command="./apply_abstract_config.py --server " + mpg_ips['F1-0'] +
        #                                     " --json ./abstract_cfg/T1_abstract_cfg.json", timeout=300)
        #
        # self.linux_obj_come.command(command="ls")
        # print result
    def cleanup(self):
        pass


class AbstractConfig(FunTestCase):
    test_bed_spec = None
    abstract_configs = ""

    def describe(self):
        self.set_test_details(id=4,
                              summary="Create Config File and Execute Abstract Config",
                              steps="""
                              1. Get MPG IPs
                              2. Add routes
                              """)

    def setup(self):
        self.test_bed_spec = fun_test.get_asset_manager().get_fs_spec(test_bed_name)
        fun_test.test_assert(expression=mpg_ips, message="Make sure MPG interfaces have IPs")
        abstract_config_file = fun_test.get_script_parent_directory() + '/abstract_configs.json'
        self.abstract_configs = fun_test.parse_file_to_json(abstract_config_file)

    def run(self):
        linux_obj = Linux(host_ip="qa-ubuntu-02", ssh_username="qa-admin", ssh_password="Precious1*")
        workspace = '/tmp'
        linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
        funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)

        # Get FunControlPlane
        fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
        fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
        linux_obj.command("cd "+workspace+"/FunControlPlane/scripts/docker/combined_cfg/abstract_cfg")
        for f1 in mpg_ips:
            file_name = f1+"_abstract.json"
            file_contents = self.abstract_configs[f1]
            linux_obj.create_file(file_name=file_name, contents=json.dumps(file_contents))
            linux_obj.command("cd "+workspace+"/FunControlPlane/scripts/docker/combined_cfg/")
            fun_test.test_assert(expression=linux_obj.command("./apply_abstract_config.py --server "+mpg_ips[f1]+
                                                              " --json ./abstract_cfg/"+file_name),
                                 message="Execute abstract config on %s" % f1)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BootFS())
    ts.add_test_case(BringupFunCP())
    ts.add_test_case(ConfigureFunCPMpgIP())
    ts.add_test_case(AbstractConfig())
    ts.run()
