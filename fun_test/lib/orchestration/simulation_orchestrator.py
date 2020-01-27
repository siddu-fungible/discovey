from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from lib.host.fio import Fio
from lib.host.host import Qemu
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1, DockerF1
from orchestrator import OrchestratorType, Orchestrator


class DockerContainerOrchestrator(Linux, Orchestrator):
    INSTANCE_TYPE_QEMU = "INSTANCE_TYPE_QEMU"
    INSTANCE_TYPE_FSU = "INSTANCE_TYPE_FSU"
    # An orchestrator (which happens to be a container) that is capable of spinning an F1 and multiple Qemu instances, all within one container

    QEMU_BASE_DIRECTORY = "/qemu"
    QEMU_DIRECTORY = "/qemu/FunQemu-Linux/bin"
    QEMU_PROCESS = "qemu-system-x86_64"
    docker_host = None
    QEMU_INTERNAL_PORTS = [50001, 50002, 50003, 50004]
    QEMU_INSTANCE_PORT = 2220

    QEMU_FS = "{}/fun-image-x86-64-qemux86-64.ext4".format(QEMU_BASE_DIRECTORY)
    QEMU_KERNEL = "{}/bzImage".format(QEMU_BASE_DIRECTORY)

    QEMU_NCPUS = 2
    QEMU_BIOS = "{}/qemu-Linux/share".format(QEMU_BASE_DIRECTORY)
    QEMU_LOG = "/tmp/qemu.log"

    QEMU_MODULES_TGZ = "modules.tgz"
    QEMU_FUNCP_TGZ = "functrlp_posix.tgz"

    FUNCP_EXTRACT_LIST = ["build/posix/lib/libfunq.so", "build/posix/bin/funq-setup", "build/posix/bin/dpc"]



    HOST_OS_DEFAULT = "fungible_yocto"
    HOST_OS_FUNGIBLE_YOCTO = {"name": "fungible_yocto", "username": "root", "password": "fun123", "connect_retry_timeout": 30}
    HOST_OS_FUNGIBLE_UBUNTU = {"name": "fungible_ubuntu", "username": "stack", "password": "stack", "connect_retry_timeout": 60}

    HOST_IMAGE_PATH = "{}/host_os".format(QEMU_BASE_DIRECTORY)  # used if want ubuntu instead of yocto
    HOST_USERNAME_DEFAULT = "root"
    HOST_PASSWORD_DEFAULT = "fun123"
    VM_HOST_OS_DEFAULT = "fungible_yocto"



    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER

    def __init__(self, **kwargs):
        # a = super(DockerContainerOrchestrator, self)
        Linux.__init__(self, host_ip=None, ssh_port=None, ssh_username=None, ssh_password=None)
        Orchestrator.__init__(self, id=kwargs["id"])

        self.container_asset = None
        self.docker_host = kwargs["docker_host"]
        self.dut_instance = None
        self.host_instances = []

    def describe(self):
        self.docker_host.describe()

    def setup_storage_container(self, dut_index, dut_obj):
        fun_test.simple_assert(self.docker_host, "Docker host available")
        if not fun_test.get_environment_variable("DOCKER_URL"):
            fun_test.simple_assert(self.docker_host.health()["result"], "Health of the docker host")

        vm_host_os = None  # TODO: Hack needed until asset_manager is implemented
        if dut_obj.interfaces:
            peer_info = dut_obj.interfaces[0].peer_info
            if hasattr(peer_info, "vm_host_os"):
                vm_host_os = peer_info.vm_host_os

        fun_test.log("Setting up the integration container for index: {}".format(dut_index))
        container_name = "{}_{}_{}".format("integration_basic", fun_test.get_suite_execution_id(), dut_index)

        container_asset = self.docker_host.setup_storage_container(container_name=container_name,
                                                                   ssh_internal_ports=[22],
                                                                   qemu_internal_ports=self.QEMU_INTERNAL_PORTS,
                                                                   dpcsh_internal_ports=[F1.INTERNAL_DPCSH_PORT],
                                                                   vm_host_os=vm_host_os)
        fun_test.simple_assert(self.docker_host.wait_for_handoff(container_name=container_name,
                                                                 handoff_string="Idling"), message="Container handoff")

        container_asset["host_type"] = self.docker_host.type  # DESKTOP, BARE_METAL

        fun_test.test_assert(container_asset, "Setup storage basic container: {}".format(container_name))
        self.ssh_username = container_asset["mgmt_ssh_username"]
        self.ssh_port = container_asset["mgmt_ssh_port"]
        self.ssh_password = container_asset["mgmt_ssh_password"]
        self.host_ip = container_asset["host_ip"]
        return container_asset

    def get_host_ssh_ports(self):  # Qemu ssh ports
        return self.container_asset["pool1_ports"]

    @fun_test.safe
    def launch_dut_instance(self, dut_index, dut_obj, already_deployed=False):
        if not self.container_asset:
            self.container_asset = self.setup_storage_container(dut_index=dut_index, dut_obj=dut_obj)
        external_dpcsh_port = self.container_asset["pool2_ports"][0]["external"]
        f1_obj = DockerF1(host_ip=self.container_asset["host_ip"],
                          ssh_username=self.container_asset["mgmt_ssh_username"],
                          ssh_password=self.container_asset["mgmt_ssh_password"],
                          ssh_port=self.container_asset["mgmt_ssh_port"],
                          external_dpcsh_port=external_dpcsh_port)
        f1_obj.set_data_plane_ip(data_plane_ip=self.container_asset["internal_ip"])

        # Start FunOS
        fun_test.test_assert(f1_obj.start(start_mode=dut_obj.start_mode),
                             "DockerContainerOrchestrator: Start FunOS")
        self.dut_container_asset = self.container_asset
        return f1_obj


    @fun_test.safe
    def launch_host_instance(self,
                             internal_ssh_port=None,
                             external_ssh_port=None,
                             qemu_num_cpus=2,
                             qemu_memory=256,
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
                          '-device virtio-blk-pci,drive=rootfs -net user,hostfwd=tcp::{}-:22 -net user,hostfwd=tcp::40220-:40220 -net nic,model=virtio'.\
                    format(self.QEMU_PROCESS, qemu_num_cpus, qemu_memory, self.QEMU_BIOS, self.QEMU_KERNEL, qemu_memory,
                           self.QEMU_FS, internal_ssh_port)
            elif vm_host_os == self.HOST_OS_FUNGIBLE_UBUNTU["name"]:
                command = './{} {} -daemonize -vnc :1 -smp {} -m {} ' \
                          '-device nvme-rem-fe -machine q35 ' \
                          '-net user,hostfwd=tcp::{}-:22 -net nic,model=virtio -enable-kvm'.format(self.QEMU_PROCESS, self.HOST_IMAGE_PATH,
                                                                 qemu_num_cpus, 2048,  # TODO
                                                                 internal_ssh_port)

            self.start_bg_process(command=command, output_file=self.QEMU_LOG)

            fun_test.sleep("Qemu startup", seconds=65)
            i = Qemu(host_ip=self.host_ip,
                     ssh_username=host_username,
                     ssh_password=host_password,
                     ssh_port=external_ssh_port,
                     connect_retry_timeout_max=60)  # TODO

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
            i.exit_sudo()
            # Don't need to reload the nvme driver while bringing up the setup. If driver reload is required it has to
            # be taken care inside the test cases. Avoiding this reload will avoid the bug #SWOS-3822
            # i.nvme_restart()
            instance = i
            self.host_instances.append(instance)
        except Exception as ex:
            fun_test.critical(str(ex))
            self.command("cat {}".format(self.QEMU_LOG))
        return instance

    def post_init(self):
        self.port_redirections = []
        self.TO_DICT_VARS.extend(["port_redirections", "ORCHESTRATOR_TYPE", "docker_host"])

    def cleanup(self):
        fun_test.add_checkpoint("Removing dut_instance")

        artifact_file_name = fun_test.get_test_case_artifact_file_name(
            post_fix_name="{}_f1.log.txt".format(self.id))
        container_asset = self.docker_host.get_container_asset(name=self.container_asset["name"])
        if container_asset:
            fun_test.scp(source_ip=container_asset["host_ip"],
                         source_file_path=F1.F1_LOG,
                         source_username=container_asset["mgmt_ssh_username"],
                         source_password=container_asset["mgmt_ssh_password"],
                         source_port=container_asset["mgmt_ssh_port"],
                         target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description="F1 Log {}".format(self.id), filename=artifact_file_name)

        # Removing host_instance

        for index, host_instance in enumerate(self.host_instances):
            fun_test.add_checkpoint("Removing host_instance {}".format(index))
            if hasattr(self, "QEMU_LOG"):
                artifact_file_name = fun_test.get_test_case_artifact_file_name(
                    post_fix_name="{}_{}_qemu.log.txt".format(self.id, index))
                fun_test.scp(source_ip=container_asset["host_ip"],
                             source_file_path=self.QEMU_LOG,
                             source_username=container_asset["mgmt_ssh_username"],
                             source_password=container_asset["mgmt_ssh_password"],
                             source_port=container_asset["mgmt_ssh_port"],
                             target_file_path=artifact_file_name)
                fun_test.add_auxillary_file(description="QEMU Log {}".format(self.id),
                                            filename=artifact_file_name)

        fun_test.sleep("Destroying container: {}".format(self.container_asset["name"]))
        self.docker_host.destroy_container(self.container_asset["name"])


class DockerHostOrchestrator(Orchestrator, DockerHost):
    # A Docker Linux Host capable of launching docker container instances
    ORCHESTRATOR_TYPE = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST
    container_assets = {}

    def __init__(self, **kwargs):
        Orchestrator.__init__(self, **kwargs)
        DockerHost.__init__(self, properties=kwargs["spec"])

    def launch_fio_instance(self, index):
        container_name = "{}_{}_{}".format("integration_fio", fun_test.get_suite_execution_id(), index)
        container_asset = self.setup_fio_container(container_name=container_name, ssh_internal_ports=[22])
        self.container_assets[container_asset["name"]] = container_asset
        return Fio.get(asset_properties=container_asset)

    def launch_linux_instance(self, index):
        container_name = "{}_{}_{}".format("integration_linux", fun_test.get_suite_execution_id(), index)
        container_asset = self.setup_linux_container(container_name=container_name, ssh_internal_ports=[22])
        self.container_assets[container_asset["name"]] = container_asset
        linux = Linux.get(asset_properties=container_asset)
        linux.internal_ip = container_asset["internal_ip"]
        return linux

    def cleanup(self):
        container_assets = self.container_assets
        for container_name in container_assets:
            fun_test.log("Destroying container: {}".format(container_name))
            self.destroy_container(container_name=container_name)