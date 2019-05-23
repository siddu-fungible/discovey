from lib.system.fun_test import *
from lib.host.linux import Linux


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
    DEPLOY_TIMEOUT = 1200
    LAUNCH_SCRIPT = "./integration_test/emulation/test_system.py "
    PREPARE_CMD = "{} --prepare --docker".format(LAUNCH_SCRIPT)
    DEPLOY_CONTAINER = "{} --setup --docker".format(LAUNCH_SCRIPT)
    F1_0_HANDLE = None
    F1_1_HANDLE = None

    def __int__(self, come_obj, mode=None):
        self.come_obj = Linux(host_ip=come_obj.host_ip,
                              ssh_username=come_obj.ssh_username,
                              ssh_password=come_obj.ssh_password,
                              ssh_port=come_obj.ssh_port)
        self.mode = mode

    def deploy_funcp_container(self, update_n_deploy=True, update_workspace=True):
        # check if come is up
        result = {'status': False, 'container_info': []}
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
        launch_resp = self.launch_funcp_containers()
        if not launch_resp:
            fun_test.critical("FunCP container launch failed")
            return response

        # get container names.
        get_containers = self.get_container_names()
        if not get_containers['status']:
            return result

        for cntnr in get_containers['container_name_list']:
            cntnr_obj = FunCpDockerContainer(host_ip=self.come_obj.host_ip,
                                             ssh_username=self.come_obj.ssh_username,
                                             ssh_password=self.come_obj.ssh_password,
                                             ssh_port=self.come_obj.ssh_port,
                                             name=cntnr)
            if "0" in cntnr:  # based on logic that container names will always be F1-1, F1-0
                self.F1_0_HANDLE = cntnr_obj
            else:
                self.F1_0_HANDLE = cntnr_obj
            result['container_info'].append(cntnr_obj)

        result['status'] = True
        return result

    def update_fundsk(self):
        result = False
        response = self.come_obj.check_file_directory_exists(self.FUNSDK_DIR)
        if not response:  # todo Raise fun_test.critical
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

    def launch_funcp_containers(self, mode):
        result = False
        self.enter_funsdk()
        cmd = self.DEPLOY_CONTAINER
        if mode:
            cmd += " --{}".format(self.mode)
        response = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT)
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
        result['container_name_list'] = self.come_obj.command(cmd).split("\n")
        container_count = len(result['container_name_list'])
        if container_count != self.NUM_FS_CONTAINERS:
            fun_test.critical(
                "{0} Containers should be deployed, Number of container deployed: {1}".format(self.NUM_FS_CONTAINERS,
                                                                                              container_count))
            return result
        else:
            result['status'] = True
        return result

    def clear_containers(self):
        # Stop Container F1_0
        if self.F1_0_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)
        if self.F1_1_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)

    def stop_container(self, container_name):
        cmd = "docker stop {}".format(container_name)
        self.come_obj.command(cmd)

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

    def configure_bond_interface(self):
        # set ip links down
        # configure interfaces, sudo ifconfig fpg4 15.1.1.1 netmask 255.255.255.252
        #
        pass
