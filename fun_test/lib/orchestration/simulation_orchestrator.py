from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from lib.host.fio import Fio
from lib.host.host import Qemu
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1, DockerF1
from orchestrator import OrchestratorType, Orchestrator


class SimulationOrchestrator(Linux, Orchestrator, ToDictMixin):
    QEMU_BASE_DIRECTORY = "/qemu"
    QEMU_DIRECTORY = "/home/jabraham/qemu/x86_64-softmmu"
    QEMU_PROCESS = "qemu-system-x86_64"
    QEMU_INSTANCE_PORT = 2220

    QEMU_FS = "{}/fun-image-x86-64-qemux86-64.ext4".format(QEMU_BASE_DIRECTORY)
    QEMU_KERNEL = "{}/bzImage".format(QEMU_BASE_DIRECTORY)

    QEMU_NCPUS = 2
    QEMU_BIOS = "{}/qemu-Linux/share".format(QEMU_BASE_DIRECTORY)
    QEMU_LOG = "/tmp/qemu.log"

    QEMU_MODULES_TGZ = "modules.tgz"
    QEMU_FUNCP_TGZ = "functrlp.tgz"

    FUNCP_EXTRACT_LIST = ["build/posix/lib/libfunq.so", "build/posix/bin/funq-setup", "build/posix/bin/dpc"]

    INSTANCE_TYPE_QEMU = "INSTANCE_TYPE_QEMU"
    INSTANCE_TYPE_FSU = "INSTANCE_TYPE_FSU"

    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_SIMULATION
    HOST_OS_DEFAULT = "fungible_yocto"
    HOST_OS_FUNGIBLE_YOCTO = {"name": "fungible_yocto", "username": "root", "password": "fun123", "connect_retry_timeout": 30}
    HOST_OS_FUNGIBLE_UBUNTU = {"name": "fungible_ubuntu", "username": "stack", "password": "stack", "connect_retry_timeout": 60}

    HOST_IMAGE_PATH = "{}/host_os".format(QEMU_BASE_DIRECTORY)  # used if want ubuntu instead of yocto
    HOST_USERNAME_DEFAULT = "root"
    HOST_PASSWORD_DEFAULT = "fun123"
    VM_HOST_OS_DEFAULT = "fungible_yocto"

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
                             external_ssh_port=None,
                             qemu_num_cpus=2,
                             qemu_memory=256,
                             vm_start_mode=None,
                             vm_host_os=VM_HOST_OS_DEFAULT):
        host_username = self.HOST_USERNAME_DEFAULT
        host_password = self.HOST_PASSWORD_DEFAULT
        if vm_host_os == self.HOST_OS_FUNGIBLE_YOCTO["name"]:
            host_username = self.HOST_OS_FUNGIBLE_YOCTO["username"]
            host_password = self.HOST_OS_FUNGIBLE_YOCTO["password"]
            self.connect_retry_timeout_max = self.HOST_OS_FUNGIBLE_YOCTO["connect_retry_timeout"]
        elif vm_host_os == self.HOST_OS_FUNGIBLE_UBUNTU["name"]:
            host_username = self.HOST_OS_FUNGIBLE_UBUNTU["username"]
            host_password = self.HOST_OS_FUNGIBLE_UBUNTU["password"]
            self.connect_retry_timeout_max = self.HOST_OS_FUNGIBLE_UBUNTU["connect_retry_timeout"]

        instance = None
        if not internal_ssh_port:
            internal_ssh_port = self.QEMU_INSTANCE_PORT
        try:

            qemu_process_id = self.get_process_id(process_name=self.QEMU_PROCESS)
            if qemu_process_id:
                self.kill_process(process_id=qemu_process_id, signal=9)

            self.add_path(self.QEMU_DIRECTORY)
            self.command("cd {}".format(self.QEMU_DIRECTORY))
            self.command("pwd; ls -l")

            command = ""
            if vm_host_os == self.HOST_OS_FUNGIBLE_YOCTO["name"]:
                command = './{}  -daemonize -vnc :1 -machine q35,iommu=on -smp {} -m {} ' \
                          '-L {} ' \
                          '-kernel {} ' \
                          '-append "root=/dev/vda rw highres=off ip=:::255.255.255.0:qemu-yocto:eth0:on oprofile.timer=1 console=ttyS0 console=tty0 mem={}M" ' \
                          '-drive file={},format=raw,if=none,id=rootfs ' \
                          '-device ioh3420,id=root_port1,addr=1c.0,port=1,chassis=1 ' \
                          '-device nvme-rem-fe,hu=0,controller=0,sim_id=0,bus=root_port1 -device virtio-rng-pci ' \
                          '-device virtio-blk-pci,drive=rootfs -redir tcp:{}::22 -redir tcp:40220::40220'.\
                    format(self.QEMU_PROCESS, qemu_num_cpus, qemu_memory, self.QEMU_BIOS, self.QEMU_KERNEL, qemu_memory,
                           self.QEMU_FS, internal_ssh_port)
            elif vm_host_os == self.HOST_OS_FUNGIBLE_UBUNTU["name"]:
                command = './{} {} -daemonize -vnc :1 -smp {} -m {} ' \
                          '-device nvme-rem-fe  -machine q35 ' \
                          '-redir tcp:{}::22 -redir tcp:40220::40220 -enable-kvm'.format(self.QEMU_PROCESS,
                                                                                         self.HOST_IMAGE_PATH,
                                                                                         qemu_num_cpus,
                                                                                         2048,  # TODO
                                                                                         internal_ssh_port)

            self.start_bg_process(command=command, output_file=self.QEMU_LOG)

            fun_test.sleep("Qemu startup", seconds=65)
            i = Qemu(host_ip=self.host_ip,
                     ssh_username=host_username,
                     ssh_password=host_password,
                     ssh_port=external_ssh_port,
                     connect_retry_timeout_max=60)  # TODO

            '''
            self.command("cd {}".format(self.QEMU_DIRECTORY))
            # Copying the moudles.tgz into qemu host
            self.command("scp -P {} /{} root@127.0.0.1:".format(internal_ssh_port, self.QEMU_MODULES_TGZ),
                         custom_prompts={"(yes/no)\?*": "yes"})
            # Copying the functrlp.tgz containing the FunCP pre-compiled libs and bins into qemu host
            self.command("scp -P {} /{} root@127.0.0.1:".format(internal_ssh_port, self.QEMU_FUNCP_TGZ),
                         custom_prompts={"(yes/no)\?*": "yes"})
            '''

            '''
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port),
                         custom_prompts={"(yes/no)\?*": "yes"})  # TODO: Why is this here?
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port),
                         custom_prompts={"(yes/no)\?*": "yes"})
            '''

            if vm_host_os == self.HOST_OS_FUNGIBLE_YOCTO["name"]:
                self.scp(source_file_path="/" + self.QEMU_MODULES_TGZ,
                         target_ip="127.0.0.1",
                         target_username=host_username,
                         target_password=host_password,
                         target_file_path="",
                         target_port=internal_ssh_port)

                self.scp(source_file_path="/" + self.QEMU_FUNCP_TGZ,
                         target_ip="127.0.0.1",
                         target_username=host_username,
                         target_password=host_username,
                         target_file_path="",
                         target_port=internal_ssh_port)


            # Untaring the functrlp.tgz and copying the libs & bins needed to start the dpc-server inside the qemu host
            i.enter_sudo()
            if vm_host_os == self.HOST_OS_FUNGIBLE_YOCTO["name"]:
                for file in self.FUNCP_EXTRACT_LIST:
                    i.command("tar -xzf {} {}".format(self.QEMU_FUNCP_TGZ, file))
                i.command("mkdir -p /usr/local/lib /usr/local/bin")
                i.command("cp build/posix/lib/libfunq.so /usr/local/lib/")
                i.command("cp build/posix/bin/funq-setup build/posix/bin/dpc /usr/local/bin/")

                # Deploying the moudles.tgz into qemu host
                # if the host is going to be Ubuntu for now don't need to replace the existing /lib/modules with our
                # Fungible library
                i.command("rm -rf /lib/modules")
                i.command("tar -xf {} -C /".format(self.QEMU_MODULES_TGZ))
                i.command("depmod -a")
            i.command("modprobe -r nvme")
            fun_test.sleep("modprobe -r nvme")
            i.command("modprobe nvme")
            i.exit_sudo()
            instance = i
        except Exception as ex:
            fun_test.critical(str(ex))
            self.command("cat {}".format(self.QEMU_LOG))
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
    QEMU_DIRECTORY = "/qemu/qemu-Linux/bin"
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
                 internal_ip,
                 host_type=DockerHost.TYPE_BARE_METAL):
        connect_retry_timeout = 20
        if host_type == DockerHost.TYPE_DESKTOP:
            connect_retry_timeout = 60
        super(SimulationOrchestrator, self).__init__(host_ip=host_ip,
                                                     ssh_username=ssh_username,
                                                     ssh_password=ssh_password,
                                                     ssh_port=ssh_port,
                                                     connect_retry_timeout_max=connect_retry_timeout)
        self.dpcsh_port = dpcsh_port
        self.qemu_ssh_ports = qemu_ssh_ports
        self.container_name = container_name
        self.internal_ip = internal_ip
        self.host_type = host_type

    def describe(self):
        self.docker_host.describe()

    @fun_test.safe
    def launch_dut_instance(self, spec, external_dpcsh_port):
        f1_obj = DockerF1(host_ip=self.host_ip,
                          ssh_username=self.ssh_username,
                          ssh_password=self.ssh_password,
                          ssh_port=self.ssh_port,
                          external_dpcsh_port=external_dpcsh_port,
                          spec=spec)
        f1_obj.set_data_plane_ip(data_plane_ip=self.internal_ip)

        # Start FunOS
        fun_test.test_assert(f1_obj.start(start_mode=spec["start_mode"]),
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
                                          internal_ip=asset_properties["internal_ip"],
                                          host_type=asset_properties["host_type"])
        return obj

    def post_init(self):
        # self.ip_route_add(network="10.1.0.0/16", gateway="172.17.0.1",
        #                  outbound_interface="eth0")  # Required to hack around automatic tap interface installation
        # self.ip_route_add(network="10.2.0.0/16", gateway="172.17.0.1", outbound_interface="eth0")
        self.port_redirections = []
        self.TO_DICT_VARS.extend(["port_redirections", "ORCHESTRATOR_TYPE", "docker_host"])


class DockerHostOrchestrator(Orchestrator, DockerHost):
    # A Docker Linux Host capable of launching docker container instances
    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST
    container_assets = {}

    def launch_fio_instance(self, index):
        container_name = "{}_{}_{}".format("integration_fio", fun_test.get_suite_execution_id(), index)
        container_asset = self.setup_fio_container(container_name=container_name, ssh_internal_ports=[22])
        return Fio.get(asset_properties=container_asset)

    def launch_linux_instance(self, index):
        container_name = "{}_{}_{}".format("integration_linux", fun_test.get_suite_execution_id(), index)
        container_asset = self.setup_linux_container(container_name=container_name, ssh_internal_ports=[22])
        self.container_assets[container_asset["name"]] = container_asset
        linux = Linux.get(asset_properties=container_asset)
        linux.internal_ip = container_asset["internal_ip"]
        return linux
