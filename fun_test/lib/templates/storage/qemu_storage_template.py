from lib.system.fun_test import fun_test
from lib.fun.f1 import F1, DockerF1
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
import re


class QemuStorageTemplate(object):

    STORAGE_TYPE = "NORMAL"
    IKV_TYPE = "IKV"
    DPC_SRV_LOG = "/tmp/dpc_server.log"

    def __init__(self, host, dut):
        self.host = host
        self.dut = dut

    @fun_test.safe
    def create_volume(self, size=32768, capacity=32768, device="/dev/nvme0", type=STORAGE_TYPE):

        volume_id = None

        if True:  # TODO self.topology.mode == fun_test.MODE_SIMULATION:
            # host_obj.nvme_setup()
            fun_test.log("Output of lsblk prior to test")
            self.host.command("lsblk")
            fun_test.test_assert(self.host.nvme_create_namespace(size=size, capacity=capacity, device=device),
                                 "Create Namespace")
            fun_test.sleep("Create Namespace", 10)

        # if self.topology.mode == fun_test.MODE_REAL:
        #    if host_obj:
        #        pass # nvme style
        #    else:
        #        pass # open-stack style
        return volume_id

    @fun_test.safe
    def attach_volume(self, namespace_id=1, device="/dev/nvme0", controllers=1):

        if True:  # TODO self.topology.mode == fun_test.MODE_SIMULATION:
            fun_test.test_assert(self.host.nvme_attach_namespace(namespace_id=namespace_id, controllers=controllers,
                                                                 device=device), "Attach Namespace")

            fun_test.sleep("Attach Namespace", 10)
        return True

    @fun_test.safe
    def deploy(self):

        deploy_result = False
        if True:  # TODO self.topology.mode == fun_test.MODE_SIMULATION:

            # Create volume
            fun_test.test_assert(self.create_volume(), "Create Volume")

            # Attach volume
            fun_test.test_assert(self.attach_volume(), "Attach Volume")

            deploy_result = True

        elif self.topology.mode == fun_test.MODE_REAL:
            if self.topology.platform == "OpenStack":
                pass

        return deploy_result

    @fun_test.safe
    def dd(self, input_file, output_file, block_size, count, timeout=60, **kwargs):
        return self.host.dd(input_file, output_file, block_size, count, timeout=60, **kwargs)

    @fun_test.safe
    def md5sum(self, file_name):
        return self.host.md5sum(file_name)

    @fun_test.safe
    def get_process_cmdline(self, process_name):

        process_cmdline = ""
        process_id = self.dut.get_process_id(process_name)
        if process_id:
            # command = r"echo `cat /proc/{}/cmdline | tr '\0' '\n'`".format(process_id)
            command = r"ps -p {} -o args --no-headers".format(process_id)
            process_cmdline = self.dut.command(command=command)

        return process_cmdline

    @fun_test.safe
    def start_dpcsh_proxy(self, dpcsh_tcp_proxy_path=DockerF1.DPCSH_PATH, dpcsh_tcp_proxy_name=F1.DPCSH_PROCESS_NAME,
                          dpcsh_tcp_proxy_port=F1.INTERNAL_DPCSH_PORT):
        # Killling any existing dpcsh TCP proxy server running outside the qemu host
        current_dpcsh_tcp_proxy_process_id = self.dut.get_process_id(dpcsh_tcp_proxy_name)
        if current_dpcsh_tcp_proxy_process_id:
            self.dut.kill_process(process_id=current_dpcsh_tcp_proxy_process_id)
            new_dpcsh_tcp_proxy_process_id = self.dut.get_process_id(dpcsh_tcp_proxy_name)
            fun_test.simple_assert(not new_dpcsh_tcp_proxy_process_id, "Stopped DPCSH TCP proxy")
            fun_test.sleep("Waiting for the port to be released", 60)
        dpcsh_tcp_proxy_cmd = "{}/{} --inet_sock --tcp_proxy={}".format(dpcsh_tcp_proxy_path, dpcsh_tcp_proxy_name,
                                                                        dpcsh_tcp_proxy_port)
        dpcsh_tcp_proxy_process_id = self.dut.start_bg_process(command=dpcsh_tcp_proxy_cmd,
                                                               output_file=F1.DPCSH_PROXY_LOG)
        fun_test.simple_assert(dpcsh_tcp_proxy_process_id, "Starting DPCSH TCP proxy")

        current_dpcsh_tcp_proxy_process_id = self.dut.get_process_id(F1.DPCSH_PROCESS_NAME)
        fun_test.test_assert_expected(actual=current_dpcsh_tcp_proxy_process_id, expected=dpcsh_tcp_proxy_process_id,
                                      message="Started DPCSH TCP proxy")

        return True

    @fun_test.safe
    def start_dpc_server(self, funq_setup_path="/usr/local/bin", funq_setup_name="funq-setup",
                         ld_lib_path="/usr/local/lib", dpc_srv_path="/usr/local/bin", dpc_srv_name="dpc",
                         dpcsh_tcp_proxy_path=DockerF1.DPCSH_PATH, dpcsh_tcp_proxy_name=F1.DPCSH_PROCESS_NAME,
                         dpcsh_tcp_proxy_port=F1.INTERNAL_DPCSH_PORT):

        # Starting the funq-setup bind inside the qemu host
        funq_setup_bind_cmd = "{}/{} bind".format(funq_setup_path, funq_setup_name)
        fun_test.simple_assert(self.host.command(command=funq_setup_bind_cmd), "Started funq-setup bind")

        # Starting the dpc server inside the qemu host
        dpc_srv_cmd = "env LD_LIBRARY_PATH={} {}/{}".format(ld_lib_path, dpc_srv_path, dpc_srv_name)
        dpc_srv_process_id = self.host.start_bg_process(command=dpc_srv_cmd, output_file=self.DPC_SRV_LOG)
        fun_test.simple_assert(dpc_srv_process_id, "Starting DPC Server")

        current_dpc_srv_process_id = self.host.get_process_id(dpc_srv_name)
        fun_test.test_assert_expected(actual=current_dpc_srv_process_id, expected=dpc_srv_process_id,
                                      message="Started DPC server")

        # Starting the dpcsh TCP proxy server outside the qemu host
        self.start_dpcsh_proxy(dpcsh_tcp_proxy_path=dpcsh_tcp_proxy_path, dpcsh_tcp_proxy_name=dpcsh_tcp_proxy_name,
                               dpcsh_tcp_proxy_port=dpcsh_tcp_proxy_port)
        return True

    @fun_test.safe
    def stop_dpc_server(self, funq_setup_path="/usr/local/bin", funq_setup_name="funq-setup",
                        dpc_srv_path="/usr/local/bin", dpc_srv_name="dpc", dpcsh_tcp_proxy_name=F1.DPCSH_PROCESS_NAME,
                        signal=2):

        # Stopping the dpcsh TCP proxy server running outside the qemu host
        current_dpcsh_tcp_proxy_process_id = self.dut.get_process_id(dpcsh_tcp_proxy_name)
        if current_dpcsh_tcp_proxy_process_id:
            self.dut.kill_process(process_id=current_dpcsh_tcp_proxy_process_id)
            new_dpcsh_tcp_proxy_process_id = self.dut.get_process_id(dpcsh_tcp_proxy_name)
            fun_test.simple_assert(not new_dpcsh_tcp_proxy_process_id, "Stopped DPCSH TCP proxy")
        else:
            fun_test.log("DPCSH TCP proxy is not running")

        # Stopping the dpc server running inside the qemu host
        current_dpc_srv_process_id = self.host.get_process_id(dpc_srv_name)
        if current_dpc_srv_process_id:
            self.host.kill_process(process_id=current_dpc_srv_process_id, signal=signal)
            new_dpc_srv_process_id = self.host.get_process_id(dpc_srv_name)
            fun_test.simple_assert(not new_dpc_srv_process_id, "Stopped DPC Server")
        else:
            fun_test.log("DPC server is not running")

        # Stopping the funq-setup bind running inside the qemu host
        funq_setup_unbind_cmd = "{}/{} unbind".format(funq_setup_path, funq_setup_name)
        fun_test.simple_assert(self.host.command(command=funq_setup_unbind_cmd), "Stopped funq-setup bind")

        return True

    @fun_test.safe
    def restart_dpc_server(self, funq_setup_path="/usr/local/bin", funq_setup_name="funq-setup",
                           ld_lib_path="/usr/local/lib", dpc_srv_path="/usr/local/bin", dpc_srv_name="dpc",
                           dpcsh_tcp_proxy_path=DockerF1.DPCSH_PATH, dpcsh_tcp_proxy_name=F1.DPCSH_PROCESS_NAME,
                           dpcsh_tcp_proxy_port=F1.INTERNAL_DPCSH_PORT):

        self.stop_dpc_server(funq_setup_path=funq_setup_path, funq_setup_name=funq_setup_name,
                             dpc_srv_path=dpc_srv_path, dpc_srv_name=dpc_srv_name,
                             dpcsh_tcp_proxy_name=dpcsh_tcp_proxy_name)
        fun_test.sleep("Breathing", 10)
        self.start_dpc_server(funq_setup_path=funq_setup_path, funq_setup_name=funq_setup_name, ld_lib_path=ld_lib_path,
                              dpc_srv_path=dpc_srv_path, dpc_srv_name=dpc_srv_name,
                              dpcsh_tcp_proxy_path=dpcsh_tcp_proxy_path, dpcsh_tcp_proxy_name=dpcsh_tcp_proxy_name,
                              dpcsh_tcp_proxy_port=dpcsh_tcp_proxy_port)

        return True

    @fun_test.safe
    def nvme_write(self, device, start, count, size, data, timeout=2):

        result = None
        nvme_write_cmd = "nvme write {} -s {} -c {} -z {} -d {}".format(device, start, count, size, data)
        output = self.host.command(command=nvme_write_cmd, timeout=timeout)
        match = re.search(r'(\w+):\s*(\S+)', output)
        if match:
            result = match.group(2)
        return result

    @fun_test.safe
    def nvme_read(self, device, start, count, size, data, timeout=2):

        result = None
        nvme_read_cmd = "nvme read {} -s {} -c {} -z {} -d {}".format(device, start, count, size, data)
        output = self.host.command(command=nvme_read_cmd, timeout=timeout)
        match = re.search(r'(\w+):\s*(\S+)', output)
        if match:
            result = match.group(2)
        return result

    @fun_test.safe
    def start_funos(self, funos_cmdline, timeout=5):

        self.dut.command("cd /")
        self.dut.command("./{} app=mdt_test nvfile=nvfile &> {}".format(F1.FUN_OS_SIMULATION_PROCESS_NAME, F1.F1_LOG))
        funos_process_id = self.dut.start_bg_process(command=funos_cmdline, output_file=F1.F1_LOG)
        fun_test.sleep("Ensure FunOS is started", seconds=timeout)
        funos_process_id = self.dut.get_process_id(F1.FUN_OS_SIMULATION_PROCESS_NAME)

        return funos_process_id

    @fun_test.safe
    def start_qemu(self, qemu_cmdline, qemu_dir=DockerContainerOrchestrator.QEMU_DIRECTORY,
                   qemu_process_name=DockerContainerOrchestrator.QEMU_PROCESS,
                   qemu_log=DockerContainerOrchestrator.QEMU_LOG, timeout=5):

        current_qemu_process_id = self.dut.get_process_id(qemu_process_name)
        if current_qemu_process_id:
            self.dut.kill_process(process_id=current_qemu_process_id)
            new_qemu_process_id = self.dut.get_process_id(qemu_process_name)
            fun_test.simple_assert(not new_qemu_process_id, "Stopped Qemu Host")

        self.dut.command("cd {}".format(qemu_dir))
        qemu_process_id = self.dut.start_bg_process(command=qemu_cmdline, output_file=qemu_log)
        fun_test.sleep("Ensure Qemu is started", seconds=60)
        self.dut.command("cd")
        qemu_process_id = self.dut.get_process_id(qemu_process_name)

        return qemu_process_id

    @fun_test.safe
    def reboot(self, timeout=5, retries=6):

        result = True
        disconnect = True

        # Rebooting the host
        self.stop_dpc_server()
        try:
            self.host.command(command="reboot", timeout=timeout)
        except Exception as ex:
            self.host.disconnect()
            disconnect = False

        fun_test.sleep("Waiting for the host to go down", timeout)
        if disconnect:
            self.host.disconnect()

        for i in range(retries):
            command_output = ""
            try:
                command_output = self.host.command(command="pwd", timeout=timeout)
                if command_output:
                    break
            except Exception as ex:
                fun_test.sleep("Sleeping for the host to come up from reboot", timeout)
                continue
        else:
            fun_test.critical("Host didn't came up from reboot even after {} seconds".format(retries * timeout))
            result = False

        return result
