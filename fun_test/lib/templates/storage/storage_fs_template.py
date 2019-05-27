from lib.system.fun_test import *
from lib.host.linux import Linux
import re


class FunCpDockerContainer(Linux):
    CUSTOM_PROMPT_TERMINATOR = r'# '

    def __init__(self, name, **kwargs):
        super(FunCpDockerContainer, self).__init__(**kwargs)
        self.name = name

    def _connect(self):
        super(FunCpDockerContainer, self)._connect()

        self.command("docker exec -it {} bash".format(self.name))
        self.clean()
        self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
        self.command("export PS1='{}'".format(self.CUSTOM_PROMPT_TERMINATOR), wait_until_timeout=3,
                     wait_until=self.CUSTOM_PROMPT_TERMINATOR)
        return True


MODE_END_POINT = "ep"


class StorageFsTemplate(object):
    NUM_FS_CONTAINERS = 2
    FUNSDK_DIR = "/mnt/keep/FunSDK/"
    DEFAULT_TIMEOUT = 300
    DEPLOY_TIMEOUT = 900
    BOND_BRINGUP_TIMEOUT = 300
    LAUNCH_SCRIPT = "./integration_test/emulation/test_system.py "
    PREPARE_CMD = "{} --prepare --docker".format(LAUNCH_SCRIPT)
    DEPLOY_CONTAINER_CMD = "{} --setup --docker".format(LAUNCH_SCRIPT)
    # F1_0_HANDLE = None
    # F1_1_HANDLE = None

    def __init__(self, come_obj):
        self.come_obj = come_obj
        self.container_info = {}

    def deploy_funcp_container(self, update_n_deploy=True, update_workspace=True, mode=None):
        # check if come is up
        result = {'status': False, 'container_info': {}, 'container_names': []}
        self.mode = mode
        if not self.come_obj.check_ssh():
            return result

        # get funsdk
        if update_n_deploy:
            if not self.update_fundsk():
                return result

        # prepare setup environment
        if update_workspace:
            response = self.prepare_docker()
            if not response:
                return result

        # launch containers
        launch_resp = self.launch_funcp_containers(mode)
        if not launch_resp:
            fun_test.critical("FunCP container launch failed")
            return result

        # get container names.
        get_containers = self.get_container_names()
        if not get_containers['status']:
            return result
        result['container_names'] = get_containers['container_name_list']
        for container_name in get_containers['container_name_list']:
            container_obj = FunCpDockerContainer(host_ip=self.come_obj.host_ip,
                                                 ssh_username=self.come_obj.ssh_username,
                                                 ssh_password=self.come_obj.ssh_password,
                                                 ssh_port=self.come_obj.ssh_port,
                                                 name=container_name)
            """
            if "0" in container_name:  # based on logic that container names will always be F1-1, F1-0
                self.F1_0_HANDLE = container_obj
            else:
                self.F1_1_HANDLE = container_obj
            """
            self.container_info[container_name] = container_obj

        result['container_info'] = self.container_info
        result['status'] = True
        return result

    def update_fundsk(self):
        result = False
        response = self.come_obj.check_file_directory_exists(self.FUNSDK_DIR)
        if not response:
            fun_test.critical("{} dir does not exists".format(self.FUNSDK_DIR))
            return result
        self.come_obj.command("cd {}".format(self.FUNSDK_DIR))
        self.come_obj.sudo_command("git pull", timeout=self.DEFAULT_TIMEOUT)
        if self.come_obj.exit_status() == 0:
            result = True
        return result

    def enter_funsdk(self):
        self.come_obj.command("cd {}".format(self.FUNSDK_DIR))

    def prepare_docker(self):
        result = False
        self.enter_funsdk()
        response = self.come_obj.command(self.PREPARE_CMD)
        sections = ["Cloning into 'FunSDK'",
                    "Cloning into 'fungible-host-drivers'",
                    "Cloning into 'FunControlPlane'",
                    "Prepare End"]
        for sect in sections:
            if sect not in response:
                fun_test.critical("{} message not found in container prepare logs".format(sect))
                result = False
        return result

    def launch_funcp_containers(self, mode=None):
        result = True
        self.enter_funsdk()
        cmd = self.DEPLOY_CONTAINER_CMD
        if mode:
            cmd += " --{}".format(mode)
        response = self.come_obj.command(cmd, timeout=self.DEPLOY_TIMEOUT)
        sections = ['Bring up Control Plane',
                    'Device 1dad:',
                    'move fpg interface to f0 docker',
                    'libfunq bind  End',
                    'move fpg interface to f1 docker',
                    'Bring up Control Plane dockers']

        for sect in sections:
            if sect not in response:
                fun_test.critical("{} message not found in container deployment logs".format(sect))
                result = False
        return result

    def get_container_names(self):
        result = {'status': False, 'container_name_list': []}
        cmd = "docker ps --format '{{.Names}}'"
        result['container_name_list'] = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT).split("\n")
        result['container_name_list'] = [name.strip("\r") for name in result['container_name_list']]
        container_count = len(result['container_name_list'])
        if container_count != self.NUM_FS_CONTAINERS:
            fun_test.critical(
                "{0} Containers should be deployed, Number of container deployed: {1}".format(self.NUM_FS_CONTAINERS,
                                                                                              container_count))
            return result
        else:
            result['status'] = True
        return result

    """
    def clear_containers(self):
        # Stop Container F1_0
        if self.F1_0_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)
        # Stop Container F1_1
        if self.F1_1_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)

    def stop_container(self, container_name):
        cmd = "docker stop {}".format(container_name)
        self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT)

    def get_f10_handle(self):
        handle = None
        if self.F1_0_HANDLE:
            handle = self.F1_0_HANDLE
        return handle

    def get_f11_handle(self):
        handle = None
        if self.F1_0_HANDLE:
            handle = self.F1_0_HANDLE
        return handle
    """

    def get_funcp_docker_handle(self, container_name):
        handle = None
        if container_name in self.container_info:
            handle = self.container_info[container_name]
        return handle

    def configure_bond_interface(self, container_name, name, ip, slave_interface_list = [],
                                 bond_bringup_timeout=BOND_BRINGUP_TIMEOUT, **kwargs):
        """
        :param docker_handle:
        :param slave_interface_list:
        :param bond_dict:
        :return:

        * The user has to pass all the slave interface name which will be part of bond interface in the form list
        * Bond interface name and IP are mandatory one needs to be passed
        * The other bond properties can be passed the name=value or as a dictionary at the end
        """

        container_obj = self.container_info[container_name]
        # Checking whether the two or more interfaces are passed to create the bond
        fun_test.simple_assert(len(slave_interface_list) >= 2, "Sufficient slave interfaces to form bond")

        bond_dict = {}
        bond_dict["name"] = name
        bond_dict["ip"] = ip

        if kwargs:
            for key in kwargs:
                bond_dict[key] = kwargs[key]

        if "mode" not in bond_dict:
            bond_dict["mode"] = "802.3ad"
        if "miimon" not in bond_dict:
            bond_dict["miimon"] = 0
        if "xmit_hash_policy" not in bond_dict:
            bond_dict["xmit_hash_policy"] = "layer3+4"
        if "min_links" not in bond_dict:
            bond_dict["min_links"] = 1

        # Disabling all the slave interfaces before adding them into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} down".format(interface_name))
            fun_test.simple_assert(not container_obj.exit_status(), "Disabling interface {}".format(interface_name))

        # Configuring the bond interface name
        bond_cmd = "sudo ip link add %(name)s type bond mode %(mode)s miimon %(miimon)s xmit_hash_policy " \
                   "%(xmit_hash_policy)s min_links %(min_links)s" % bond_dict
        container_obj.command(bond_cmd)
        fun_test.simple_assert(not container_obj.exit_status(), "Creating bond {} interface".
                               format(bond_dict["name"]))

        # Adding slaves interfaces into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} master {}".format(interface_name, bond_dict["name"]))
            fun_test.simple_assert(not container_obj.exit_status(), "Adding interface {} into bond {}".
                                   format(interface_name, bond_dict["name"]))

        # Enabling all the slave interfaces after adding them into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} up".format(interface_name))
            fun_test.simple_assert(not container_obj.exit_status(), "Enabling interface {}".format(interface_name))

        # Disabling the bond interface before configuring IP address to it
        bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="down")
        fun_test.simple_assert(bond_status, "Disabling {} interface".format(bond_dict["name"]))

        # Configuring IP address for the bond interface
        bond_ip_config = "sudo ip addr add %(ip)s dev %(name)s" % bond_dict
        container_obj.command(bond_ip_config)
        fun_test.simple_assert(not container_obj.exit_status(), "Configuring IP to {} interface".
                               format(bond_dict["name"]))

        # Enabling the bond interface after configuring IP address to it
        bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="up")
        fun_test.simple_assert(bond_status, "Enabling {} interface".format(bond_dict["name"]))

        # Checking whether the bond0 is UP and Running
        match = ""
        timer = FunTimer(max_time=bond_bringup_timeout)
        while not timer.is_expired():
            bond_output = container_obj.command("ifconfig {}".format(bond_dict["name"]))
            match = re.search(r'UP.*RUNNING', bond_output)
            if not match:
                fun_test.critical("{} interface is still not in running state...So going to flip it")
                bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="down")
                fun_test.sleep("Disabling {} interface".format(bond_dict["name"]), 2)
                bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="up")
                fun_test.sleep("Enabling {} interface".format(bond_dict["name"]), 2)
            else:
                break
        else:
            fun_test.simple_assert(match, "Bond {} interface is UP & RUNNING".format(bond_dict["name"]))

        return True
