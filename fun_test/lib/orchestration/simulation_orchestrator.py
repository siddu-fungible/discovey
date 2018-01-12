from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from lib.host.fio import Fio
from lib.host.host import Qemu
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1, DockerF1
from orchestrator import OrchestratorType, Orchestrator

class SimulationOrchestrator(Linux, Orchestrator, ToDictMixin):
    QEMU_PATH = "/home/jabraham/qemu/x86_64-softmmu"
    QEMU_PROCESS = "qemu-system-x86_64"
    QEMU_INSTANCE_PORT = 2220

    INSTANCE_TYPE_QEMU = "INSTANCE_TYPE_QEMU"
    INSTANCE_TYPE_FSU = "INSTANCE_TYPE_FSU"

    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_SIMULATION

    @staticmethod
    def get(asset_properties):
        s = SimulationOrchestrator(host_ip=asset_properties["host_ip"],
                                   ssh_username=asset_properties["mgmt_ssh_username"],
                                   ssh_password=asset_properties["mgmt_ssh_password"],
                                   ssh_port=asset_properties["mgmt_ssh_port"])
        s.TO_DICT_VARS.append("ORCHESTRATOR_TYPE")
        return s

    @fun_test.safe
    def launch_host_instance(self,
                             instance_type=INSTANCE_TYPE_QEMU,
                             internal_ssh_port=None,
                             external_ssh_port=None):
        instance = None
        if not internal_ssh_port:
            internal_ssh_port = self.QEMU_INSTANCE_PORT
        try:

            qemu_process_id = self.get_process_id(process_name=self.QEMU_PROCESS)
            if qemu_process_id:
                self.kill_process(process_id=qemu_process_id, signal=9)

            self.add_path(self.QEMU_PATH)
            self.command("cd {}".format(self.QEMU_PATH))
            self.command("pwd; ls -l")
            # command = './{} ubuntu_min.img -machine q35 -smp 1 -m 2048 -enable-kvm -device nvme-rem-fe,sim_id=0 -redir tcp:2220::22 -nographic'.format(self.QEMU_PROCESS)
            function = 0  # Dima: The default F1 config creates 3 PFs (AFAIR 0, 3, 7), all on HU 0, controller 0.
            if fun_test.counter:
                function = 4

            # command = "./{} -L pc-bios -daemonize -machine q35 -m 256 -device nvme-rem-fe,function={},sim_id=0 -redir tcp:{}::22 -drive file=core-image-full-cmdline-qemux86-64.ext4,if=virtio,format=raw -kernel bzImage -append 'root=/dev/vda rw ip=:::255.255.255.0:qemu-yocto:eth0:on mem=256M oprofile.timer=1'".format(self.QEMU_PROCESS, function, ssh_port)
            command = "./{} -L pc-bios -daemonize -vnc :1 -machine q35 -m 256 -device nvme-rem-fe,sim_id=0 -redir tcp:{}::22 -drive file=../core-image-full-cmdline-qemux86-64.ext4,if=virtio,format=raw -kernel ../bzImage -append 'root=/dev/vda rw ip=:::255.255.255.0:qemu-yocto:eth0:on mem=256M oprofile.timer=1'".format(
                self.QEMU_PROCESS, internal_ssh_port)

            self.start_bg_process(command=command, output_file="/tmp/qemu.log")

            fun_test.sleep("Qemu startup", seconds=65)
            i = Qemu(host_ip=self.host_ip,
                     ssh_username="root",  # stack
                     ssh_password="stack",
                     ssh_port=external_ssh_port, connect_retry_timeout_max=300)  # TODO

            self.command("cd {}".format(self.QEMU_PATH))
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port),
                         custom_prompts={"(yes/no)\?*": "yes"})  # TODO: Why is this here?
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port),
                         custom_prompts={"(yes/no)\?*": "yes"})

            instance = i
        except Exception as ex:
            fun_test.critical(str(ex))
        return instance

    @fun_test.safe
    def launch_dut_instance(self,
                            dpcsh_only,
                            external_dpcsh_port):
        f1_obj = F1(host_ip=self.host_ip,
                    ssh_username=self.ssh_username,
                    ssh_password=self.ssh_password,
                    ssh_port=self.ssh_port)

        # Start FunOS
        fun_test.test_assert(f1_obj.start(dpcsh=True,
                                          dpcsh_only=dpcsh_only),
                             "SimulationOrchestrator: Start FunOS")
        return f1_obj

    @fun_test.safe
    def launch_docker_instances(self,
                                type,
                                ):
        if type == "quagga-router":
            pass


class DockerContainerOrchestrator(SimulationOrchestrator):
    # An orchestrator (which happens to be a container) that is capable of spinning an F1 and multiple Qemu instances, all within one container
    QEMU_PATH = "/qemu/x86_64-softmmu"
    QEMU_PROCESS = "qemu-system-x86_64"
    docker_host = None

    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER

    def __init__(self,
                 host_ip,
                 ssh_username,
                 ssh_password,
                 ssh_port,
                 dpcsh_port,
                 qemu_ssh_ports,
                 container_name,
                 internal_ip):
        super(SimulationOrchestrator, self).__init__(host_ip=host_ip,
                                                     ssh_username=ssh_username,
                                                     ssh_password=ssh_password,
                                                     ssh_port=ssh_port)
        self.dpcsh_port = dpcsh_port
        self.qemu_ssh_ports = qemu_ssh_ports
        self.container_name = container_name
        self.internal_ip = internal_ip

    def describe(self):
        self.docker_host.describe()

    @fun_test.safe
    def launch_dut_instance(self, start_mode, external_dpcsh_port):
        f1_obj = DockerF1(host_ip=self.host_ip,
                          ssh_username=self.ssh_username,
                          ssh_password=self.ssh_password,
                          ssh_port=self.ssh_port)
        f1_obj.set_data_plane_ip(data_plane_ip=self.internal_ip)

        # Start FunOS
        fun_test.test_assert(f1_obj.start(start_mode=start_mode,
                                          external_dpcsh_port=external_dpcsh_port),
                             "DockerContainerOrchestrator: Start FunOS")
        return f1_obj

    @staticmethod
    def get(asset_properties):
        obj = DockerContainerOrchestrator(host_ip=asset_properties["host_ip"],
                                          ssh_username=asset_properties["mgmt_ssh_username"],
                                          ssh_password=asset_properties["mgmt_ssh_password"],
                                          ssh_port=asset_properties["mgmt_ssh_port"],
                                          dpcsh_port=asset_properties["pool2_ports"][0]["external"],
                                          qemu_ssh_ports=asset_properties["pool1_ports"],
                                          container_name=asset_properties["name"],
                                          internal_ip=asset_properties["internal_ip"])
        return obj

    def post_init(self):
        self.ip_route_add(network="10.1.0.0/16", gateway="172.17.0.1",
                          outbound_interface="eth0")  # Required to hack around automatic tap interface installation
        self.ip_route_add(network="10.2.0.0/16", gateway="172.17.0.1", outbound_interface="eth0")
        self.port_redirections = []
        self.TO_DICT_VARS.extend(["port_redirections", "ORCHESTRATOR_TYPE", "docker_host"])


class DockerHostOrchestrator(Orchestrator, DockerHost):
    # A Docker Linux Host capable of launching docker container instances
    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST

    def launch_fio_instance(self, index):
        id = index + fun_test.get_suite_execution_id()
        container_name = "{}_{}".format("integration_fio", id)
        container_asset = self.setup_fio_container(container_name=container_name, ssh_internal_ports=[22])
        return Fio.get(asset_properties=container_asset)

    def launch_linux_instance(self, index):
        id = index + fun_test.get_suite_execution_id()
        container_name = "{}_{}".format("integration_lnx", id)
        container_asset = self.setup_linux_container(container_name=container_name, ssh_internal_ports=[22])
        linux = Linux.get(asset_properties=container_asset)
        linux.internal_ip = container_asset["internal_ip"]
        return linux
