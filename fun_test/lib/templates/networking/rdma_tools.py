from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import re
import math
import os

LD_LIBRARY_PATH = "$LD_LIBRARY_PATH:/mnt/ws/fungible-rdma-core/build/lib/"
PATH = "$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/"


class Rocetools:

    def __init__(self, host):
        self.host = host

    def repo_info(self, path):
        self.host.command("cd {}".format(path))
        self.host.command("git describe")
        self.host.disconnect()

    def rdma_setup(self):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))
        check_funeth = self.host.lsmod("funeth")
        if not check_funeth:
            fun_test.critical("Funeth load status")
            return False
        check_module = self.host.lsmod("funrdma")
        if not check_module:
            self.host.sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko")
        check_module = self.host.lsmod("funrdma")
        if not check_module:
            fun_test.test_assert(False, "Funrdma load failed")
            return False
        else:
            self.host.modprobe("rdma_ucm")
            self.host.disconnect()
        return True

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

    def ib_bw_test(self, test_type, server_ip=None, timeout=60, **kwargs):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))

        if test_type == "write":
            tool = "ib_write_bw "
        elif test_type == "read":
            tool = "ib_read_bw "
        cmd_str = tool + "--report_gbits -F -d funrdma0 "

        if "duration" in kwargs:
            cmd_str += "-D " + str(kwargs["duration"])
            del kwargs["duration"]
        else:
            cmd_str += "-D 10"
        if "size" in kwargs:
            cmd_str += " -s " + str(kwargs["size"])
            del kwargs["size"]
        if "bidi" in kwargs:
            cmd_str += "-b"
            del kwargs["bidi"]
        if "qpair" in kwargs:
            cmd_str += " -q " + str(kwargs["qpair"])
            del kwargs["qpair"]
        if "cq_mod" in kwargs:
            cmd_str += " -Q " + str(kwargs["cq_mod"])
            del kwargs["cq_mod"]
        if "rdma_cm" in kwargs:
            if kwargs["rdma_cm"]:
                cmd_str += " -R"
            del kwargs["rdma_cm"]
        if "perf" in kwargs:
            # cmd_str += " --run_infinitely"
            del kwargs["perf"]
        if server_ip:
            cmd_str += " " + str(server_ip) + " "
            output_file = "/tmp/{}".format(tool.strip()) + "_client"
        else:
            output_file = "/tmp/{}".format(tool.strip()) + "_server"

        if kwargs:
            for key in kwargs:
                cmd_str += " " + str(kwargs[key])

        fun_test.debug(cmd_str)
        cmd_pid = self.host.start_bg_process(command=cmd_str, nohup=False, output_file=output_file, timeout=timeout)
        result_dict = {"cmd_pid": cmd_pid, "output_file": output_file}
        return result_dict

    def ib_lat_test(self, test_type, server_ip=None, timeout=60, **kwargs):
        self.host.command("export LD_LIBRARY_PATH={}".format(LD_LIBRARY_PATH))
        self.host.command("export PATH={}".format(PATH))

        if test_type == "write":
            tool = "ib_write_lat "
        elif test_type == "read":
            tool = "ib_read_lat "
        cmd_str = tool + "-I 64 -F -d funrdma0 "

        if "iteration" in kwargs:
            cmd_str += "-n " + str(kwargs["iteration"])
            del kwargs["iteration"]
        else:
            cmd_str += "-n 10000"
        if "size" in kwargs:
            cmd_str += " -s " + str(kwargs["size"])
            del kwargs["size"]
        if "bidi" in kwargs:
            cmd_str += " -b"
            del kwargs["bidi"]
        if "qpair" in kwargs:
            cmd_str += " -q " + str(kwargs["qpair"])
            del kwargs["qpair"]
        if "cq_mod" in kwargs:
            cmd_str += " -Q " + str(kwargs["cq_mod"])
            del kwargs["cq_mod"]
        if "rdma_cm" in kwargs:
            if kwargs["rdma_cm"]:
                cmd_str += " -R"
            del kwargs["rdma_cm"]
        if "perf" in kwargs:
            # cmd_str += " --run_infinitely"
            del kwargs["perf"]
        if server_ip:
            cmd_str += " " + str(server_ip) + " "
            output_file = "/tmp/{}".format(tool.strip()) + "_client"
        else:
            output_file = "/tmp/{}".format(tool.strip()) + "_server"

        if kwargs:
            for key in kwargs:
                cmd_str += " " + str(kwargs[key])

        fun_test.debug(cmd_str)
        cmd_pid = self.host.start_bg_process(command=cmd_str, nohup=False, output_file=output_file, timeout=timeout)
        result_dict = {"cmd_pid": cmd_pid, "output_file": output_file}
        return result_dict

    def parse_test_log(self, filepath, tool=None, client_cmd=None, perf=None):
        # Make sure there is a space during pattern match, as it will match address like 0x55ea98bad090
        error_pattern = "error|fatal|mismatch|fail|assert|\bbad\b"

        content = self.host.command("cat {}".format(filepath))
        match_error_list = re.findall(r'{}'.format(error_pattern), content, re.IGNORECASE)
        if match_error_list:
            fun_test.critical("Found error string: {}".format(match_error_list))
            return False

        # Parse rping & srping results
        if tool == "srping" or tool == "rping":
            if client_cmd:
                client_events = ["RDMA_CM_EVENT_ADDR_RESOLVED", "RDMA_CM_EVENT_ROUTE_RESOLVED",
                                 "RDMA_CM_EVENT_ESTABLISHED", "destroy"]
                list_client_events = "RDMA_CM_EVENT_ADDR_RESOLVED|RDMA_CM_EVENT_ROUTE_RESOLVED|" \
                                     "RDMA_CM_EVENT_ESTABLISHED|destroy"
                match_event_list = re.findall(r'{}'.format(list_client_events), content, re.IGNORECASE)

                for event in client_events:
                    if event not in match_event_list:
                        fun_test.critical("Event {} not found on client".format(event))
                        return False
                return True
            else:
                server_events = ["RDMA_CM_EVENT_CONNECT_REQUEST", "RDMA_CM_EVENT_ESTABLISHED",
                                 "RDMA_CM_EVENT_DISCONNECTED", "destroy"]
                list_server_events = "RDMA_CM_EVENT_CONNECT_REQUEST|RDMA_CM_EVENT_ESTABLISHED|" \
                                     "RDMA_CM_EVENT_DISCONNECTED|destroy"
                match_event_list = re.findall(r'{}'.format(list_server_events), content, re.IGNORECASE)

                for event in server_events:
                    if event not in match_event_list:
                        fun_test.critical("Event {} not found on server".format(event))
                        return False
                return True
        elif tool == "ib_bw":
            # TODO to overcome the cleanup issue and get past scaling we are not using run_infinitely. So changing grep
            # line to 1
            if perf:
                grep_line = 1
            else:
                grep_line = 1
            # content = self.host.command("grep -i 'bytes' -A {} {} | tail -1".format(grep_line, filepath))
            content = self.host.command("grep -i 'bytes' -A {} {} | tail -1".format(grep_line, filepath))
            lines = content.split()
            total_values = len(lines)
            for x in range(0, total_values):
                if lines[x] == "inf" or math.isinf(float(lines[x])):
                    lines[x] = -1
            size = lines[0]
            iterations = lines[1]
            bw_peak = lines[2]
            bw_avg = lines[3]
            pps = lines[4]
            if bw_avg == 0.0 or bw_avg == 0.0 or iterations == 0:
                self.host.command("dmesg")
                self.host.disconnect()
                fun_test.test_assert(False, "BW test failed as result is zero!!")
                return False
            if perf:
                return lines
        elif tool == "ib_lat":
            if perf:
                # content = self.host.command("grep -i 'bytes' -A 3 {} | tail -1".format(filepath))
                content = self.host.command("grep -i 'bytes' -A 1 {} | tail -1".format(filepath))
                lines = content.split()
                total_values = len(lines)
                for x in range(0, total_values):
                    if lines[x] == "inf" or math.isinf(float(lines[x])):
                        lines[x] = -1

                size = lines[0]
                iterations = lines[1]
                t_min = lines[2]
                t_max = lines[3]
                t_typical = lines[4]
                t_avg = lines[5]
                t_stdev = lines[6]
                t_99 = lines[7]
                t_9999 = lines[8]
            else:
                content = self.host.command("grep -i 'bytes' -A 1 {} | tail -1".format(filepath))
                lines = content.split()
                total_values = len(lines)
                for x in range(0, total_values):
                    if lines[x] == "inf" or math.isinf(float(lines[x])):
                        lines[x] = -1
                size = lines[0]
                iterations = lines[1]
                t_min = lines[2]
                t_max = lines[3]
                t_typical = lines[4]
                t_avg = lines[5]
                t_stdev = lines[6]
                t_99 = lines[7]
                t_9999 = lines[8]
            if t_min == 0.0 or t_max == 0.0 or t_avg == 0.0 or iterations == 0:
                self.host.command("dmesg")
                self.host.disconnect()
                fun_test.test_assert(False, "Latency test failed as result is zero!!")
                return False
            if perf:
                return lines

        return True

    def kill_pid(self, pid):
        self.host.kill_process(process_id=pid)
        self.host.disconnect()

    def process_check(self, pid):
        return self.host.process_exists(process_id=pid)

    def qp_check(self):
        qp_count = int(self.host.sudo_command(command="cat /sys/kernel/debug/funrdma/*/qps | wc -l").strip())
        return qp_count

    def cleanup(self):
        self.host.sudo_command(command="killall -g ib_write_lat ib_write_bw ib_read_lat ib_read_bw srping rping")
        self.host.disconnect()

    def build_rdma_repo(self, rdmacore_branch=None, rdmacore_commit=None, perftest_branch=None, perftest_commit=None,
                        perf_build=True, ws="/mnt/ws"):
        self.rdmacore_branch = rdmacore_branch
        self.rdmacore_commit = rdmacore_commit
        self.perftest_branch = perftest_branch
        self.perftest_commit = perftest_commit
        self.ws = ws

        sdkdir = os.path.join(self.ws, 'FunSDK')

        # Clone fungible-perftest & rdma-core
        self.host.command("cd {} ; git clone git@github.com:fungible-inc/fungible-perftest.git".format(self.ws))
        self.host.command("cd {} ; git clone git@github.com:fungible-inc/fungible-rdma-core.git".format(self.ws))
        rdma_perf_test_path = self.ws + "/fungible-perftest"
        rdma_core_path = self.ws + "/fungible-rdma-core"

        if perftest_branch:
            self.host.command("cd {} ; git checkout {}".format(rdma_perf_test_path, perftest_branch))
        if perftest_commit:
            self.host.command("cd {} ; git checkout {}".format(rdma_perf_test_path, perftest_commit))
        if rdmacore_branch:
            self.host.command("cd {} ; git checkout {}".format(rdma_core_path, rdmacore_branch))
        if perftest_commit:
            self.host.command("cd {} ; git checkout {}".format(rdma_core_path, rdmacore_commit))
        if perf_build:
            self.host.command("export WORKSPACE={}".format(self.ws))
            cmd_pid = self.host.command(
                command="cd {} ; EXTRA_CMAKE_FLAGS=-DCMAKE_BUILD_TYPE=Release PALLADIUM=yes ./build.sh".
                format(rdma_core_path), timeout=600)
        else:
            self.host.command("export WORKSPACE={}".format(self.ws))
            output = self.host.command(
                command="cd {} ; EXTRA_CMAKE_FLAGS=-DCMAKE_BUILD_TYPE=RelWithDebInfo PALLADIUM=yes ./build.sh".
                format(rdma_core_path), timeout=600)
        self.host.command("export WORKSPACE={}".format(self.ws))
        output = self.host.command(command="cd {} ; ./fungible-build.sh".format(rdma_perf_test_path),
                                   timeout=600)
        self.host.disconnect()

