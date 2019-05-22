from lib.system.fun_test import *
from lib.host.linux import Linux


class FunCpDockerContainer(Linux):
    CUSTOM_PROMPT_TERMINATOR = r'# '

    def __init__(self, f1_index, **kwargs):
        super(FunCpDockerContainer, self).__init__(**kwargs)
        self.f1_index = f1_index

    def _connect(self):
        super(FunCpDockerContainer, self)._connect()

        self.command("docker exec -it F1-{} bash".format(self.f1_index))
        self.clean()
        self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
        self.command("export PS1='{}'".format(self.CUSTOM_PROMPT_TERMINATOR), wait_until_timeout=3,
                     wait_until=self.CUSTOM_PROMPT_TERMINATOR)
        return True


class StorageFsTemplate(object):
    MODE_END_POINT = "ep"
    FUNSDK_DIR = "/mnt/keep/FunSDK/"
    DEFAULT_TIMEOUT = 1200
    F1_0_CONTAINER = None
    F1_1_CONTAINER = None

    def __int__(self, come_obj, mode=MODE_END_POINT):
        self.come_obj = Linux(host_ip=come_obj.host_ip,
                              ssh_username=come_obj.ssh_username,
                              ssh_password=come_obj.ssh_password,
                              ssh_port=come_obj.ssh_port)

    def deploy_fun_cp_container(self, prepare=True):
        # check if come is up
        result = {'status': False}
        if not self.come_obj.check_ssh():
            return result
        # get funsdk
        if not self.update_fundsk():
            return result
        # bring up containe
        if prepare:
            response = self.prepare_docker()
            if not response:
                return result
        launch_resp = self.launch_funcp_containers()
        if not launch_resp:
            fun_test.critical("FunCP container launch failed")
            return response

        # get container names.
        get_containers = self.get_container_names()
        if not get_containers['status']:
            return result
        result['status'] = True
        result['container_name_list'] = get_containers['container_list']
        return result

    def get_container_names(self):
        result = {'status': False, 'container_list': []}
        cmd = "docker ps --format '{{.Names}}'"
        result['container_list'] = self.come_obj.command(cmd).split("\n")
        container_count = len(result['container_list'])
        if container_count != 2:
            fun_test.critical(
                "2 Containers should be deplyed, Number of container deployed: {}".format(container_count))
            return result
        else:
            result['status'] = True
        return result

    def update_fundsk(self):
        result = False
        response = self.come_obj.check_file_directory_exists(self.FUNSDK_DIR)
        if not response:
            return result
        self.come_obj.command("cd {}".format(self.FUNSDK_DIR))
        self.come_obj.sudo_command("git pull", timeout=120)
        if self.come_obj.exit_status == 0:
            result = True
        return result

    def enter_funsdk(self):
        self.come_obj.command("cd {}".format(self.FUNSDK_DIR))

    def prepare_docker(self):
        result = False
        self.enter_funsdk()
        continer_cmd = "./integration_test/emulation/test_system.py --prepare --docker"
        response = self.come_obj.command(continer_cmd)
        sections = ['Cloning into \'FunSDK\'',
                    'Cloning into \'fungible-host-drivers\'',
                    'Cloning into \'FunControlPlane\'',
                    'Prepare End']
        for sect in sections:
            if sect not in response:
                fun_test.critical("{} not seen in container deplyment logs".format(sect))
                result = False
        return result

    def launch_funcp_containers(self):
        result = False
        self.enter_funsdk()
        cmd = "./integration_test/emulation/test_system.py --setup --docker"
        response = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT)
        sections = ['Bring up Control Plane',
                    'Device 1dad:',
                    'move fpg interface to f0 docker',
                    'libfunq bind  End',
                    'move fpg interface to f1 docker',
                    'Bring up Control Plane dockers']

        for sect in sections:
            if sect not in response:
                fun_test.critical("{} not seen in container deplyment logs".format(sect))
                result = False
        return result

    def clear_containers(self):
        # get list of all created containers
        # execute docker rm
        pass

    def execute_container_cmd(self, container_name, cmd):
        pass

    def configure_bond_interface(self):
        # set ip links down
        # configure interfaces, sudo ifconfig fpg4 15.1.1.1 netmask 255.255.255.252
        #
        pass
