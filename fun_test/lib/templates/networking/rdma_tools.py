from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import re

LD_LIBRARY_PATH = "/mnt/ws/fungible-rdma-core/build/lib/"
PATH = "$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/"


class Rocetools:

    def __init__(self, host):
        self.host = host

    def repo_info(self, path):
        self.host.command("cd {}".format(path))
        self.host.command("git describe")

    def rdma_setup(self):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))
        check_module = self.host.lsmod("funrdma")
        if not check_module:
            self.host.sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko")
        check_module = self.host.lsmod("funrdma")
        if not check_module:
            fun_test.test_assert(False, "Funrdma load failed")
        else:
            self.host.modprobe("rdma_ucm")

    def get_rdma_device(self):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))
        ibv_dev = self.host.command("ibv_devices")
        if "funrdma0" in ibv_dev:
            fun_test.log("Funrdma device present")
            ibdevice = "funrdma0"

    def srping_test(self, server_ip=None, debug=False, timeout=120, **kwargs):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))

        if server_ip:
            cmd_str = "srping -ca " + str(server_ip) + " -V"
            output_file = "/tmp/srping_client.log"
        else:
            cmd_str = "srping -sV"
            output_file = "/tmp/srping_server.log"
        if "size" in kwargs:
            cmd_str += " -S " + str(kwargs["size"])
            del kwargs["size"]
        if "count" in kwargs:
            cmd_str += " -C " + str(kwargs["count"])
            del kwargs["count"]
        if debug:
            cmd_str += " -d "

        if kwargs:
            for key in kwargs:
                if key not in cmd_str:
                    cmd_str += " " + str(kwargs[key])
        fun_test.debug(cmd_str)
        cmd_pid = self.host.start_bg_process(command=cmd_str, nohup=False, output_file=output_file, timeout=timeout)
        result_dict = {"cmd_pid": cmd_pid, "output_file": output_file}
        return result_dict

        fun_test.debug(cmd_pid)

    def rping_test(self, server_ip=None, debug=False, timeout=120, **kwargs):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))

        if server_ip:
            cmd_str = "rping -ca " + str(server_ip) + " -V"
            output_file = "/tmp/rping_client.log"
        else:
            cmd_str = "rping -sV"
            output_file = "/tmp/rping_server.log"
        if "size" in kwargs:
            cmd_str += " -S " + str(kwargs["size"])
            del kwargs["size"]
        if "count" in kwargs:
            cmd_str += " -C " + str(kwargs["count"])
            del kwargs["count"]
        if debug:
            cmd_str += " -d "

        if kwargs:
            for key in kwargs:
                if key not in cmd_str:
                    cmd_str += " " + str(kwargs[key])
        fun_test.debug(cmd_str)
        cmd_pid = self.host.start_bg_process(command=cmd_str, nohup=False, output_file=output_file, timeout=timeout)
        result_dict = {"cmd_pid": cmd_pid, "output_file": output_file}
        return result_dict

        fun_test.debug(cmd_pid)

    def bw_test(self, test_type, server_ip, duration=30, timeout=60, **kwargs):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))

        if test_type == "write":
            tool = "ib_write_bw "
        elif test_type == "read":
            tool = "ib_read_bw "
        cmd_str = tool + "-F -d funrdma0 -D " + duration

        if kwargs:
            for key in kwargs:
                cmd_str += " " + str(kwargs[key])

        fun_test.debug(cmd_str)

        # Executing the command
        cmd_result = self.command(command=cmd_str, timeout=timeout)
        fun_test.debug(cmd_result)

    def parse_test_log(self, filepath):
        #error_pattern = "error|fatal|mismatch|fail|assert|bad"
        error_pattern = "error|fatal|mismatch|fail|assert|bad"
        cm_destroy = "destroy"
        cm_established ="RDMA_CM_EVENT_ESTABLISHED"
        content = self.host.command("cat {}".format(filepath))

        match_error_list = re.findall(r'{}'.format(error_pattern), content, re.IGNORECASE)
        if match_error_list:
            fun_test.critical("Found error string: {}".format(match_error_list))
            return False
        else:
            return True

        # match_destroy = re.search(r'{}'.format(cm_destroy), content)
        # match_established = re.search(r'{}'.format(cm_established), content)
        # if match_established and match_destroy:
        #     return True
        # if not match_destroy:
        #     fun_test.critical("destroy: Event not found")
        # if not match_established:
        #     fun_test.critical("RDMA_CM_EVENT_ESTABLISHED: Event not found")

    def cleanup(self):
        self.host.sudo_command(command="killall -g ib_write_lat ib_write_bw ib_read_lat ib_read_bw srping rping")
