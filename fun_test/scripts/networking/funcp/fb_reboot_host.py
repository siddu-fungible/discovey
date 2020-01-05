from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from scripts.storage.storage_helper import *
from asset.asset_manager import *
import re
import socket


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def reboot_host(arg1):
    arg1.reboot(max_wait_time=400)


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def cleanup(self):
        pass


class SetupInfo(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS with control plane",
                              steps="""
                                  1. BringUP both F1s
                                  2. Bringup FunCP
                                  3. Create MPG Interfaces and assign static IPs
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fun_test.shared_variables["fio"] = {}
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "reboot_count" in job_inputs:
            reboot_count = job_inputs["reboot_count"]
            fun_test.shared_variables["reboot_count"] = reboot_count
        else:
            reboot_count = 100
            fun_test.shared_variables["reboot_count"] = reboot_count
        fun_test.log("Running reboot test for {} iterations".format(reboot_count))
        if "run_fio" in job_inputs:
            run_fio = job_inputs["run_fio"]
            fun_test.shared_variables["run_fio"] = run_fio
        else:
            fun_test.shared_variables["run_fio"] = True

        topology_helper = TopologyHelper()

        # Get COMe object
        am = AssetManager()
        th = TopologyHelper(spec=am.get_test_bed_spec(name=fs_name))
        topology = th.get_expanded_topology()
        dut = topology.get_dut(index=0)
        dut_name = dut.get_name()
        fs_spec = fun_test.get_asset_manager().get_fs_spec(name=dut_name)
        fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True)
        come_obj = fs_obj.get_come()
        fun_test.shared_variables["come_obj"] = come_obj

        fun_test.log("Getting host info")
        host_dict = {"f1_0": [], "f1_1": []}
        temp_host_list = []
        temp_host_list1 = []
        expanded_topology = topology_helper.get_expanded_topology()
        pcie_hosts = expanded_topology.get_pcie_hosts_on_interfaces(dut_index=0)
        for pcie_interface_index, host_info in pcie_hosts.iteritems():
            host_instance = fun_test.get_asset_manager().get_linux_host(host_info["name"])
            if pcie_interface_index <= 11:
                if host_info["name"] not in temp_host_list:
                    host_dict["f1_0"].append(host_instance)
                    temp_host_list.append(host_info["name"])
            elif pcie_interface_index > 11 <= 23:
                if host_info["name"] not in temp_host_list1:
                    host_dict["f1_1"].append(host_instance)
                    temp_host_list1.append(host_info["name"])
        fun_test.shared_variables["hosts_obj"] = host_dict

        fun_test.shared_variables["host_len_f10"] = len(host_dict["f1_0"])
        fun_test.shared_variables["host_len_f11"] = len(host_dict["f1_1"])

        f10_hosts = []
        f11_hosts = []
        for objs in host_dict:
            for handle in host_dict[objs]:
                handle.sudo_command("dmesg -c > /dev/null")
                hostname = handle.command("hostname").strip()
                if objs == "f1_0":
                    f10_host_dict = {"name": hostname, "handle": handle}
                    f10_hosts.append(f10_host_dict)
                elif objs == "f1_1":
                    f11_host_dict = {"name": hostname, "handle": handle}
                    f11_hosts.append(f11_host_dict)
        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts

        fun_test.log("SETUP Done")

    def cleanup(self):
        pass


class RebootTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Reboot F10 hosts and run fio",
                              steps="""
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        reboot_count = fun_test.shared_variables["reboot_count"]
        fio_seq_tests = ["write", "read"]
        fio_rand_test = ["randwrite", "randread"]
        run_fio = fun_test.shared_variables["run_fio"]
        seq_fio_cmd_args = {"size": "5G", "verify": "pattern", "verify_pattern": "\\\"DEADBEEF\\\"",
                            "verify_fatal": 1, "bs": "4k", "timeout": 240}
        rand_fio_cmd_args = {"size": "5G", "verify": "pattern", "verify_pattern": "\\\"DEADCAFE\\\"",
                             "verify_fatal": 1, "bs": "4k", "timeout": 360}

        for count in xrange(1, reboot_count + 1):
            print "================="
            print "Iteration {}".format(count)
            print "================="

            if run_fio:
                # Start seq fio traffic on F1_0 hosts
                for test in fio_seq_tests:
                    host_index = 1
                    thread_id = {}
                    for obj in f10_hosts:
                        thread_id[host_index] = fun_test.execute_thread_after(time_in_seconds=2,
                                                                              func=fio_parser,
                                                                              arg1=obj["handle"],
                                                                              host_index=host_index,
                                                                              rw=test,
                                                                              numjobs=1,
                                                                              iodepth=8,
                                                                              direct=1,
                                                                              cpus_allowed="8-12",
                                                                              filename="/tmp/seq_test.img",
                                                                              **seq_fio_cmd_args)
                        host_index += 1
                        fun_test.sleep("Fio threadzz", seconds=1)

                    fun_test.sleep("Sleeping between thread join...", seconds=10)
                    for x in xrange(1, host_index):
                        fun_test.log("Joining thread {}".format(x))
                        fun_test.join_thread(fun_test_thread_id=thread_id[x])

                # Start rand fio traffic on F1_0 hosts
                for test in fio_rand_test:
                    host_index = 1
                    thread_id = {}
                    for obj in f10_hosts:
                        thread_id[host_index] = fun_test.execute_thread_after(time_in_seconds=2,
                                                                              func=fio_parser,
                                                                              arg1=obj["handle"],
                                                                              host_index=host_index,
                                                                              rw=test,
                                                                              direct=1,
                                                                              numjobs=1,
                                                                              iodepth=8,
                                                                              cpus_allowed="8-12",
                                                                              filename="/tmp/rand_test.img",
                                                                              **rand_fio_cmd_args)
                        host_index += 1
                        fun_test.sleep("Fio threadzz", seconds=1)
                    fun_test.sleep("Sleeping between thread join...", seconds=10)
                    for x in xrange(1, host_index):
                        fun_test.log("Joining thread {}".format(x))
                        fun_test.join_thread(fun_test_thread_id=thread_id[x])
                    fun_test.sleep("Pause before next tests", 10)

            # Reboot hosts in threaded mode
            host_index = 1
            thread_id = {}
            for obj in f10_hosts:
                thread_id[host_index] = fun_test.execute_thread_after(time_in_seconds=1,
                                                                      func=reboot_host,
                                                                      arg1=obj["handle"])
                host_index += 1

            fun_test.sleep("Sleeping between thread join...", seconds=10)
            for x in xrange(1, host_index):
                fun_test.log("Joining reboot thread {}".format(x))
                fun_test.join_thread(fun_test_thread_id=thread_id[x])

            for obj in f10_hosts:
                host_os = obj["handle"].command("cat /etc/redhat-release")
                if "centos" not in host_os.lower():
                    fun_test.test_assert(False, "Machine booted to Ubuntu")

            # Check PCIe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"),
                                     message="Make sure that PCIe links on host %s went up"
                                             % server)
                if result == "2":
                    fun_test.add_checkpoint(
                        "<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                        % servers_mode[server])

        fun_test.log("Test done")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(SetupInfo())
    ts.add_test_case(RebootTest())
    ts.run()
