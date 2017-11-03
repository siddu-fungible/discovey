from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from lib.host.host import Qemu
from lib.fun.f1 import F1, DockerF1


class SimulationOrchestrator(Linux, ToDictMixin):
    QEMU_PATH = "/home/jabraham/qemu/x86_64-softmmu"
    QEMU_PROCESS = "qemu-system-x86_64"
    QEMU_INSTANCE_PORT = 2220

    INSTANCE_TYPE_QEMU = "INSTANCE_TYPE_QEMU"
    INSTANCE_TYPE_FSU = "INSTANCE_TYPE_FSU"

    ORCHESTRATOR_TYPE = "SimulationOrchestrator"

    @staticmethod
    def get(asset_properties):
        s = SimulationOrchestrator(host_ip=asset_properties["host_ip"],
                                      ssh_username=asset_properties["mgmt_ssh_username"],
                                      ssh_password=asset_properties["mgmt_ssh_password"],
                                      ssh_port=asset_properties["mgmt_ssh_port"])
        s.TO_DICT_VARS.append("ORCHESTRATOR_TYPE")
        return s


    @fun_test.log_parameters
    def launch_instance(self,
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
            command = "./{} -L pc-bios -daemonize -vnc :1 -machine q35 -m 256 -device nvme-rem-fe,sim_id=0 -redir tcp:{}::22 -drive file=core-image-full-cmdline-qemux86-64.ext4,if=virtio,format=raw -kernel bzImage -append 'root=/dev/vda rw ip=:::255.255.255.0:qemu-yocto:eth0:on mem=256M oprofile.timer=1'".format(self.QEMU_PROCESS, internal_ssh_port)

            self.start_bg_process(command=command, output_file="/tmp/qemu.log")

            fun_test.sleep("Qemu startup", seconds=65)
            i = Qemu(host_ip=self.host_ip,
                      ssh_username="root", # stack
                      ssh_password="stack",
                      ssh_port=external_ssh_port, connect_retry_timeout_max=300)  # TODO

            self.command("cd {}".format(self.QEMU_PATH))
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port), custom_prompts={"(yes/no)\?*": "yes"}) #TODO
            self.command("scp -P {}  nvme*.ko root@127.0.0.1:/".format(internal_ssh_port), custom_prompts={"(yes/no)\?*": "yes"})

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

    @fun_test.log_parameters
    def launch_docker_instances(self,
                                type,
                                ):
        if type == "quagga-router":
            pass


class DockerContainerOrchestrator(SimulationOrchestrator):
    QEMU_PATH = "/qemu"
    QEMU_PROCESS = "qemu-system-x86_64"
    docker_host = None

    ORCHESTRATOR_TYPE = "DockerContainerOrchestrator"

    def describe(self):
        self.docker_host.describe()

    @fun_test.safe
    def launch_dut_instance(self, dpcsh_only, external_dpcsh_port):
        f1_obj = DockerF1(host_ip=self.host_ip,
                    ssh_username=self.ssh_username,
                    ssh_password=self.ssh_password,
                    ssh_port=self.ssh_port)

        # Start FunOS
        fun_test.test_assert(f1_obj.start(dpcsh=True,
                                          dpcsh_only=dpcsh_only,
                                            external_dpcsh_port = external_dpcsh_port),
                             "DockerContainerOrchestrator: Start FunOS")
        return f1_obj


    def get_redir_port(self):
        docker_host = self.docker_host
        ssh_port = docker_host.get_next_qemu_ssh_port()
        return ssh_port

    @staticmethod
    def get(asset_properties, docker_host):
        prop = asset_properties
        obj = DockerContainerOrchestrator(host_ip=prop["host_ip"],
                                      ssh_username=prop["mgmt_ssh_username"],
                                      ssh_password=prop["mgmt_ssh_password"],
                                      ssh_port=prop["mgmt_ssh_port"])
        obj.docker_host = docker_host
        obj.internal_ip = asset_properties["internal_ip"]
        obj.dpcsh_port = asset_properties["dpcsh_port"]
        obj.qemu_ssh_ports = asset_properties["qemu_ssh_ports"]
        return obj

    def post_init(self):
        # self.docker_host = self.host_ip
        self.ip_route_add(network="10.1.0.0/16", gateway="172.17.0.1", outbound_interface="eth0")
        self.ip_route_add(network="10.2.0.0/16", gateway="172.17.0.1", outbound_interface="eth0")
        self.port_redirections = []
        self.TO_DICT_VARS.extend(["port_redirections", "ORCHESTRATOR_TYPE", "docker_host"])

    def add_port_redir(self, port, internal_ip):
        docker_host = self.docker_host
        docker_host.iptables(table=Linux.IPTABLES_TABLE_NAT,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_DOCKER,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             destination_port=port,
                             action=Linux.IPTABLES_ACTION_DNAT, nat_to_destination="{}:{}".format(internal_ip, port))

        # docker_host.command("iptables -t nat -A DOCKER -p tcp --dport 2220 -j DNAT --to-destination 172.17.0.2:2220")
        #docker_host.command(
        #    "iptables -t nat -A POSTROUTING -j MASQUERADE -p tcp --source 172.17.0.2 --destination 172.17.0.2 --dport 2220")

        docker_host.iptables(table=Linux.IPTABLES_TABLE_NAT,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_POSTROUTING,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             source_ip=internal_ip,
                             action=Linux.IPTABLES_ACTION_MASQUERADE,
                             destination_ip=internal_ip,
                             destination_port=port)

        docker_host.iptables(action=Linux.IPTABLES_ACTION_ACCEPT,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             destination_ip=internal_ip,
                             destination_port=port,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_DOCKER
                             )
        # docker_host.command("iptables -A DOCKER -j ACCEPT -p tcp --destination 172.17.0.2 --dport 2220")
        self.port_redirections = [[port, internal_ip]]
        docker_host.allocate_qemu_ssh_port(port=port, internal_ip=internal_ip)

class DockerHostOrchestrator(SimulationOrchestrator):
    ORCHESTRATOR_TYPE = "DockerHostOrchestrator"
