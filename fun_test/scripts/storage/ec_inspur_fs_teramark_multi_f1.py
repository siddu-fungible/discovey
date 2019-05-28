from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.templates.storage.storage_fs_template import *
from ec_perf_helper import *

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volumes = fun_test.shared_variables["num_volumes"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volumes, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


class ECVolumeLevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 2
            self.command_timeout = 5
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        if not hasattr(self, "dut_start_index"):
            self.dut_start_index = 0
        if not hasattr(self, "host_start_index"):
            self.host_start_index = 0
        if not hasattr(self, "update_workspace"):
            self.update_workspace = False
        if not hasattr(self, "update_deploy_script"):
            self.update_deploy_script = False

        job_inputs = fun_test.get_job_inputs()
        print("job inputs is: {}".format(job_inputs))
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
            print("inside job inputs: dut_start_index: {}".format(self.dut_start_index))
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
            print("inside job inputs: host_Start_index: {}".format(self.host_start_index))
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
            print("inside job inputs: prepare_fucnp: {}".format(self.update_workspace))
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]

        fun_test.log("Global Config: {}".format(self.__dict__))

        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        self.testbed_config = fun_test.get_asset_manager().get_test_bed_spec(self.testbed_type)
        fun_test.log("{} Testbed Config: {}".format(self.testbed_type, self.testbed_config))
        self.total_avaialble_duts = len(self.testbed_config["dut_info"])
        print("total_avaialble_duts are: {}".format(self.total_avaialble_duts))

        self.num_duts = (self.num_f1s / self.num_f1_per_fs)
        print("num_dut is: {}".format(self.num_duts))

        fun_test.test_assert(expression=self.num_duts <= self.total_avaialble_duts, message="Testbed has enough DUTs")

        # Skipping DUTs not required for this test
        self.skip_dut_list = []
        for index in xrange(0, self.dut_start_index):
            self.skip_dut_list.append(index)
        for index in xrange(self.dut_start_index+self.num_duts, self.total_avaialble_duts):
            self.skip_dut_list.append(index)
        print("skip dut list is: {}".format(self.skip_dut_list))

        topology_helper = TopologyHelper()
        topology_helper.disable_duts(self.skip_dut_list)
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                          1: {"boot_args": self.bootargs[1]}})
        topology = topology_helper.deploy()
        print("topology output is: {}".format(topology.spec))
        fun_test.test_assert(topology, "Topology deployed")
        try:
            print("topology spec: {}".format(topology.spec))
        except:
            pass

        self.db_log_time = get_data_collection_time()
        fun_test.log("Data collection time: {}".format(self.db_log_time))

        fun_test.log("Hosts")
        hosts = topology.get_hosts()
        print ("Available hosts are: {}".format(hosts))

        required_host_index = []
        required_host_names = []
        for i in xrange(self.host_start_index, self.host_start_index + self.num_hosts):
            required_host_index.append(i)
        print ("required_host_index: {}".format(required_host_index))
        for j, host_name in enumerate(sorted(hosts)):
            if j in required_host_index:
                required_host_names.append(host_name)
        print ("required_host_names: {}".format(required_host_names))

        self.hosts_test_interfaces = []
        self.host_handles = {}
        self.host_ips = []
        self.host_numa_cpus = {}
        for host_name, host in hosts.items():
            if host_name in required_host_names:
                print ("host are: {}".format(host))
                print ("host dir: {}".format(dir(host)))
                print ("host_name are: {}".format(host_name))
                print ("host_name dir: {}".format(dir(host_name)))
                test_interfaces = host.get_test_interfaces()
                print ("test_interfaces: {}".format(test_interfaces))

                test_interface_0 = host.get_test_interface(index=0)
                self.hosts_test_interfaces.append(host.get_test_interface(index=0))
                print ("host_obj is: {}".format(self.hosts_test_interfaces))
                print ("host_obj dir is: {}".format(dir(self.hosts_test_interfaces)))

                print ("test_interface_0 : {}".format(test_interface_0))
                print ("test_interface_0 dir : {}".format(dir(test_interface_0)))
                print ("test_interface_0 type: {}".format(type(test_interface_0)))

                fun_test.log("Host-IP: {}".format(test_interface_0.ip))
                host_ip = self.hosts_test_interfaces[-1].ip.split('/')[0]
                # host_ip = test_interface_0.ip
                self.host_ips.append(host_ip)

                fun_test.log("Peer-info: {}".format(test_interface_0.peer_info))
                fun_test.log("Switch-name: {}".format(test_interface_0.peer_info["name"]))
                fun_test.log("Switch-port: {}".format(test_interface_0.peer_info["port"]))

                host_instance = host.get_instance()
                print ("hosts_instance: {}".format(host_instance))
                print ("hosts_instance dir: {}".format(dir(host_instance)))
                self.host_handles[host_ip] = host_instance
                # host_instance.command("date")

        print ("hosts_instances: {}".format(self.host_handles))
        print ("hosts_instances dir: {}".format(dir(self.host_handles)))
        print ("host_ips are: {}".format(self.host_ips))

        # Rebooting all the hosts in non-blocking mode before the test
        for key in self.host_handles:
            self.host_numa_cpus[key] = fetch_numa_cpus(self.host_handles[key], self.ethernet_adapter)
            fun_test.log("Rebooting host: {}".format(key))
            self.host_handles[key].reboot(non_blocking=True)
        print ("host_nma_cpus is: {}".format(self.host_numa_cpus))

        # Getting FS, F1 and COMe objects for all the DUTs going to be used in the test
        self.fs_obj = []
        self.fs_spec = []
        self.come_obj = []
        self.f1_obj = {}
        self.sc_obj = []
        self.f1_ips = []
        self.gateway_ips = []
        for i in xrange(self.dut_start_index, self.dut_start_index + self.num_duts):
            curr_index = i - self.dut_start_index
            self.fs_obj.append(topology.get_dut_instance(index=i))
            self.fs_spec.append(topology.get_dut(index=i))
            self.come_obj.append(self.fs_obj[curr_index].get_come())
            try:
                print("fs_obj[{}] is: {}".format(curr_index, self.fs_obj[curr_index]))
            except:
                pass
            try:
                print("fs_obj[{}] is: {}".format(curr_index, dir(self.fs_obj[curr_index])))
            except:
                pass
            try:
                print("come_obj[{}] is: {}".format(curr_index, self.come_obj[curr_index]))
            except:
                pass
            try:
                print("come_obj[{}] is: {}".format(curr_index, dir(self.come_obj[curr_index])))
            except:
                pass
            try:
                print("fs_spec[{}] is: {}".format(curr_index, self.fs_spec[curr_index]))
            except:
                pass
            try:
                print("fs_spec.spec[{}] is: {}".format(curr_index, self.fs_spec[curr_index].spec))
            except:
                pass
            self.f1_obj[curr_index] = []
            # self.f1_ips[curr_index] = []  # TODO: check
            # self.sc_obj[curr_index] = []  # TODO: Check
            # self.gateway_ips[curr_index] = []  # TODO: check
            for j in xrange(self.num_f1_per_fs):
                self.f1_obj[curr_index].append(self.fs_obj[curr_index].get_f1(index=j))
                self.sc_obj.append(self.f1_obj[curr_index][j].get_dpc_storage_controller())
                # self.sc_obj[curr_index].append(self.f1_obj[curr_index][j].get_dpc_storage_controller)  # TODO: Check

                fpg_interfaces = self.fs_spec[curr_index].get_fpg_interfaces(f1_index=j)
                for fpg_interface_index, fpg_interface in fpg_interfaces.items():
                    peer_end_point = fpg_interface.get_peer_instance()
                    fun_test.log(
                        "F1 index: {} FPG Interface: {} IP: {}".format(fpg_interface.f1_index, fpg_interface_index,
                                                                       fpg_interface.ip))
                fun_test.log("Bond Interfaces:")
                bond_interfaces = self.fs_spec[curr_index].get_bond_interfaces(f1_index=j)
                for bond_interface_index, bond_interface in bond_interfaces.items():
                    print("Dir of bond_interface is: {}".format(dir(bond_interface)))
                    fun_test.log("Bond interface index: {}".format(bond_interface_index))
                    fun_test.log("IP: {}".format(bond_interface.ip))
                    bond_interface_ip = bond_interface.ip
                    self.f1_ips.append(bond_interface_ip.split('/')[0])
                    # self.f1_ips[curr_index].append(bond_interface_ip.split('/')[0])  # TODO Check
                    # self.gateway_ips[curr_index].append(self.f1_ips[curr_index].replace(r'\.\d+$', '.1'))  # TODO check
                    fpg_slaves = bond_interface.fpg_slaves
                    fun_test.log("FPG slaves: {}".format(fpg_slaves))

                    for fpg_slave_index in fpg_slaves:
                        fpg_interface = self.fs_spec[curr_index].get_fpg_interface(f1_index=j,
                                                                                   interface_index=fpg_slave_index)
                        fun_test.log("Slave index: {} - FPG Interface: {}".format(fpg_slave_index, fpg_interface))

                try:
                    print("f1_obj[{}][{}] is: {}".format(curr_index, j, self.f1_obj[curr_index][j]))
                except:
                    pass
                try:
                    print("f1_obj[{}][{}] is: {}".format(curr_index, j, dir(self.f1_obj[curr_index][j])))
                except:
                    pass
                try:
                    print ("storage_controller object list is: {}".format(self.sc_obj[-1]))
                    print ("dir of storage_controller object list is: {}".format(dir(self.sc_obj[-1])))
                except:
                    pass
                try:
                    print ("F1 IP is: {}".format(self.f1_ips[-1]))
                except:
                    pass

        """
        # Enabling network controller to listen in the given F1 ip and port
        for index, sc in enumerate(self.sc_obj):
            print ("storage controller list is: {}".format(sc))
            print ("dir of storage controller list is: {}".format(dir(sc)))
            command_result = sc.ip_cfg(ip=self.f1_ips[index], port=1099)
            fun_test.test_assert(command_result["status"],
                                 "Enabling controller to listen in {} on {} port in {} DUT".
                                 format(self.f1_ips[index], 1099, index))"""

        fun_test.shared_variables["fs_obj"] = self.fs_obj
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_obj
        fun_test.shared_variables["sc_obj"] = self.sc_obj
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        # Bringing up of FunCP docker container if it is needed
        if "workarounds" in self.testbed_config and "enable_funcp" in self.testbed_config["workarounds"] and \
                self.testbed_config["workarounds"]["enable_funcp"]:
            self.funcp_obj = {}
            self.funcp_spec = {}
            for index in xrange(self.num_duts):
                self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
                self.funcp_spec[index] = self.funcp_obj[index].deploy_funcp_container(
                    update_n_deploy=self.update_deploy_script, update_workspace=self.update_workspace,
                    mode=self.funcp_mode)
                fun_test.test_assert(self.funcp_spec[index]["status"],
                                     "Starting FunCP docker container in DUT {}".format(index))
                self.funcp_spec[index]["container_names"].sort()
                for f1_index, container_name in enumerate(sorted(self.funcp_spec[index]["container_names"])):
                    bond_interfaces = self.fs_spec[index].get_bond_interfaces(f1_index=f1_index)
                    bond_name = "bond0"
                    bond_ip = bond_interfaces[0].ip
                    slave_interface_list = bond_interfaces[0].fpg_slaves
                    slave_interface_list = ["fpg" + str(i) for i in slave_interface_list]
                    self.funcp_obj[index].configure_bond_interface(container_name=container_name,
                                                                   name=bond_name,
                                                                   ip=bond_ip,
                                                                   slave_interface_list=slave_interface_list)
            print ("funcp_spec is: {}".format(self.funcp_spec))
            print ("dir of funcp_spec is: {}".format(dir(self.funcp_spec)))
            print ("type of funcp_spec is: {}".format(type(self.funcp_spec)))

            print ("funcp_obj is: {}".format(self.funcp_obj))
            print ("dir of funcp_obj is: {}".format(dir(self.funcp_obj)))
            print ("type of funcp_obj is: {}".format(type(self.funcp_obj)))
        else:
            pass

        hosts_up_count = 0
        for key in self.host_handles:
            # Ensure hosts are up after reboot
            # TODO: check reboot timeout
            fun_test.test_assert(self.host_handles[key].ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                 message="Ensure Host is reachable after reboot")
            hosts_up_count += 1

            # TODO: enable after mpstat check is added
            """
            # Check and install systat package
            install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
            fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
            """

            # Ensure required modules are loaded on host server, if not load it
            for module in self.load_modules:
                module_check = self.host_handles[key].lsmod(module)
                if not module_check:
                    self.host_handles[key].modprobe(module)
                    module_check = self.host_handles[key].lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        # TODO: Assert of critical message?
        fun_test.test_assert_expected(expected=self.num_hosts, actual=hosts_up_count, message="Required hosts are up")

        # Adding Static route and Ensuring Host is able to ping to both FunCP containers
        # TODO: Should we add gateway IP in hosts.json or we should derive it?
        """
        f1_gateway_ip = []
        f1_gateway_ip = self.f1_ips[index].replace(r'\.\d+$', '.1')
        """
        gateway_ip = ["15.43.1.1", "15.43.2.1"]
        for index in xrange(self.num_duts):
            for f1_index, container_name in enumerate(sorted(self.funcp_spec[index]["container_names"])):
                try:
                    self.funcp_obj[index].container_info[container_name].command("hostname")
                    cmd = "sudo ip route add 15.0.0.0/8 via {} dev {}".format(gateway_ip[f1_index], bond_name)
                    route_add_status = self.funcp_obj[index].container_info[container_name].command(cmd)
                    print ("static route add output is: {}".format(route_add_status))

                    """
                    # Configuring Static route
                    self.funcp_obj[index].container_info[container_name].ip_route_add(network="15.0.0.0/8",
                                                                                      gateway=gateway_ip[f1_index],
                                                                                      outbound_interface=bond_name,
                                                                                      timeout=self.command_timeout)
                    """
                    """fun_test.test_assert_expected(
                        expected=0, actual=self.funcp_obj[index].container_info[container_name].exit_status(),
                        message="Configure static route")"""
                except:
                    print ("in except: failed")

        for key in self.host_handles:
            for index, ip in enumerate(self.f1_ips):
                ping_status = self.host_handles[key].ping(dst=ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(key, self.funcp_spec[0]["container_names"][index], ip))

        """
        before funcp code: get the host handles, reboot hosts (non blocking) - check nvme and nvme_tcp module is loaded
        add static route in both dockers
        get host handles and ping both the bond
        """

        """ Old code
        self.fs = topology.get_dut_instance(index=self.f1_in_use)
        self.db_log_time = get_data_collection_time()

        self.come = self.fs.get_come()
        self.storage_controller = StorageController(target_ip=self.come.host_ip,
                                                    target_port=self.come.get_dpc_port(self.f1_in_use))

        # Fetching Linux host with test interface name defined
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if self.testbed_type == "fs-6" and host_ip != "poc-server-01":
                continue
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                self.end_host = host_info["host_obj"]
                self.test_interface_name = self.end_host.extra_attributes["test_interface_name"]
                self.fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(self.fpg_inteface_index))
                break
        else:
            fun_test.test_assert(False, "Host found with Test Interface")

        self.test_network = self.csr_network[str(self.fpg_inteface_index)]
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["test_network"] = self.test_network
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Fetching NUMA node from Network host for mentioned Ethernet Adapter card
        lspci_output = self.end_host.lspci(grep_filter=self.ethernet_adapter)
        fun_test.simple_assert(lspci_output, "Ethernet Adapter Detected")
        adapter_id = lspci_output[0]['id']
        fun_test.simple_assert(adapter_id, "Ethernet Adapter Bus ID Retrieved")
        lspci_verbose_output = self.end_host.lspci(slot=adapter_id, verbose=True)
        numa_node = lspci_verbose_output[0]['numa_node']
        fun_test.test_assert(numa_node, "Ethernet Adapter NUMA Node Retrieved")

        # Fetching NUMA CPUs for above fetched NUMA Node
        lscpu_output = self.end_host.lscpu(grep_filter="node{}".format(numa_node))
        fun_test.simple_assert(lscpu_output, "CPU associated to Ethernet Adapter NUMA")

        self.numa_cpus = lscpu_output.values()[0]
        fun_test.test_assert(self.numa_cpus, "CPU associated to Ethernet Adapter NUMA")
        fun_test.log("Ethernet Adapter: {}, NUMA Node: {}, NUMA CPU: {}".format(self.ethernet_adapter, numa_node,
                                                                                self.numa_cpus))

        fun_test.shared_variables["numa_cpus"] = self.numa_cpus

        # Configuring Linux host
        host_up_status = self.end_host.reboot(timeout=self.command_timeout, max_wait_time=self.reboot_timeout)
        fun_test.test_assert(host_up_status, "End Host {} is up".format(self.end_host.host_ip))

        interface_ip_config = "ip addr add {} dev {}".format(self.test_network["test_interface_ip"],
                                                             self.test_interface_name)
        interface_mac_config = "ip link set {} address {}".format(self.test_interface_name,
                                                                  self.test_network["test_interface_mac"])
        link_up_cmd = "ip link set {} up".format(self.test_interface_name)
        static_arp_cmd = "arp -s {} {}".format(self.test_network["test_net_route"]["gw"],
                                               self.test_network["test_net_route"]["arp"])

        interface_ip_config_status = self.end_host.sudo_command(command=interface_ip_config,
                                                                timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Configuring test interface IP address")

        interface_mac_status = self.end_host.sudo_command(command=interface_mac_config,
                                                          timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Assigning MAC to test interface")

        link_up_status = self.end_host.sudo_command(command=link_up_cmd, timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Bringing up test link")

        interface_up_status = self.end_host.ifconfig_up_down(interface=self.test_interface_name,
                                                             action="up")
        fun_test.test_assert(interface_up_status, "Bringing up test interface")

        route_add_status = self.end_host.ip_route_add(network=self.test_network["test_net_route"]["net"],
                                                      gateway=self.test_network["test_net_route"]["gw"],
                                                      outbound_interface=self.test_interface_name,
                                                      timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="Adding route to F1")

        arp_add_status = self.end_host.sudo_command(command=static_arp_cmd, timeout=self.command_timeout)
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(),
                                      message="Adding static ARP to F1 route")

        # Loading the nvme and nvme_tcp modules
        self.end_host.modprobe(module="nvme")
        fun_test.sleep("Loading nvme module", 2)
        command_result = self.end_host.lsmod(module="nvme")
        fun_test.simple_assert(command_result, "Loading nvme module")
        fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

        self.end_host.modprobe(module="nvme_tcp")
        fun_test.sleep("Loading nvme_tcp module", 2)
        command_result = self.end_host.lsmod(module="nvme_tcp")
        fun_test.simple_assert(command_result, "Loading nvme_tcp module")
        fun_test.test_assert_expected(expected="nvme_tcp", actual=command_result['name'],
                                      message="Loading nvme_tcp module")"""

    def cleanup(self):

        pass
        """
        try:
            self.ec_info = fun_test.shared_variables["ec_info"]
            self.remote_ip = fun_test.shared_variables["remote_ip"]
            self.attach_transport = fun_test.shared_variables["attach_transport"]
            self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
            if fun_test.shared_variables["ec"]["setup_created"]:
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid, ns_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume on DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                unconfigure_ec_volume(storage_controller=self.storage_controller, ec_info=self.ec_info,
                                      command_timeout=self.command_timeout)

                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Storage Controller Delete")
        except Exception as ex:
            fun_test.critical(str(ex))

        self.storage_controller.disconnect()
        fun_test.sleep("Allowing buffer time before clean-up", 30)
        fun_test.shared_variables["topology"].cleanup()"""


class ECVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        # End of benchmarking json file parsing

        self.fs_obj = fun_test.shared_variables["fs_obj"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1_obj = fun_test.shared_variables["f1_obj"]
        self.sc_obj = fun_test.shared_variables["sc_obj"]
        self.f1_ips = fun_test.shared_variables["f1_ips"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.host_numa_cpus = fun_test.shared_variables["numa_cpus"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.syslog_level = fun_test.shared_variables["syslog_level"]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"]

        # fun_test.shared_variables["attach_transport"] = self.attach_transport
        # num_ssd = self.num_ssd
        # fun_test.shared_variables["num_ssd"] = num_ssd

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            """command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")"""

            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.ec_info["num_volumes"]:
                for i in range(len(self.host_ips), self.ec_info["num_volumes"]):
                    self.final_host_ips.append(self.host_ips[len(self.host_ips) % i])

            self.ec_info["storage_controller_list"] = self.sc_obj
            self.ec_info["f1_ips"] = self.f1_ips
            self.ec_info["host_ips"] = self.final_host_ips
            (ec_config_status, self.ec_info) = configure_ec_volume_across_f1s(self.ec_info, self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
            print ("ec_config_status output is: {}".format(ec_config_status))
            print ("dir of ec_config_status output is: {}".format(dir(ec_config_status)))

            # Test - return
            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))
            fun_test.shared_variables["ec"]["setup_created"] = True

            # Setting the syslog level
            for index, sc in enumerate(self.sc_obj):
                command_result = sc.poke(props_tree=["params/syslog/level", self.syslog_level], legacy=False,
                                         command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Setting syslog level to {} on {} DUT".
                                     format(self.syslog_level, index))

        if not fun_test.shared_variables["ec"]["nvme_connect"]:
            self.connected_nqn = []
            self.nvme_block_device_list = {}
            for num in range(self.ec_info["num_volumes"]):
                host_ip = self.final_host_ips[num]
                self.nvme_block_device_list[host_ip] = []
                current_nqn = self.ec_info["attach_nqn"][num]
                hosting_f1 = self.ec_info["hosting_f1_list"][num]
                hosting_f1_ip = self.f1_ips[hosting_f1]
                if current_nqn not in self.connected_nqn:
                    self.connected_nqn.append(current_nqn)
                    # Checking nvme-connect status
                    if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}".format(
                            self.attach_transport.lower(), hosting_f1_ip, str(self.transport_port),
                            current_nqn, host_ip)
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                            self.attach_transport.lower(), hosting_f1_ip, str(self.transport_port), current_nqn,
                            str(self.io_queues), host_ip)

                    nvme_connect_status = self.host_handles[host_ip].sudo_command(command=nvme_connect_cmd,
                                                                                  timeout=self.command_timeout)
                    fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
                    fun_test.test_assert_expected(expected=0, actual=self.host_handles[host_ip].exit_status(),
                                                  message="NVME Connect Status from Host {} to F1 {}".
                                                  format(host_ip, hosting_f1_ip))

                    # TODO: Check the capacity of attached devices
                    lsblk_output = self.host_handles[host_ip].lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")

                    # Checking that the above created BLT volume is visible to the end host
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                                     str(match.group(2))
                            self.nvme_block_device_list[host_ip].append(self.nvme_block_device)
                            self.volume_name = self.nvme_block_device.replace("/dev/", "")
                            break
                    else:
                        fun_test.test_assert(False, "{} device available".format(self.volume_name))
                    fun_test.log("NVMe Block Device/s: {}".format(self.nvme_block_device_list))

                fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
                fun_test.shared_variables["volume_name"] = self.volume_name
                fun_test.shared_variables["ec"]["nvme_connect"] = True

            # Executing the FIO command to fill the volume to it's capacity
            if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
                for host_ip in self.nvme_block_device_list:
                    fio_filename = ":".join(self.nvme_block_device_list[host_ip])
                    fun_test.log("Executing the FIO command to perform sequential write to volume")
                    fio_output = self.host_handles[host_ip].pcie_fio(filename=fio_filename,
                                                                     cpus_allowed=self.host_numa_cpus[host_ip],
                                                                     **self.warm_up_fio_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "Pre-populating the volume")

                    fun_test.shared_variables["ec"]["warmup_io_completed"] = True

            """
            # Attaching/Exporting all the EC/LS volumes to the external server
            self.remote_ip = self.test_network["test_interface_ip"].split('/')[0]
            fun_test.shared_variables["remote_ip"] = self.remote_ip

            self.ctrlr_uuid = utils.generate_uuid()
            command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                       transport=self.attach_transport,
                                                                       remote_ip=self.remote_ip,
                                                                       nqn=self.nvme_subsystem,
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create Storage Controller for {} with controller uuid {} on DUT".
                                 format(self.attach_transport, self.ctrlr_uuid))

            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                    ns_id=num + 1, vol_uuid=self.ec_info["attach_uuid"][num], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                          command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

        if not fun_test.shared_variables["ec"]["nvme_connect"]:
            # Checking nvme-connect status
            if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                                 self.test_network["f1_loopback_ip"],
                                                                                 str(self.transport_port),
                                                                                 self.nvme_subsystem)
            else:
                nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {}".format(
                    self.attach_transport.lower(), self.test_network["f1_loopback_ip"], str(self.transport_port),
                    self.nvme_subsystem, str(self.io_queues))

            nvme_connect_status = self.end_host.sudo_command(command=nvme_connect_cmd, timeout=self.command_timeout)
            fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
            fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

            lsblk_output = self.end_host.lsblk("-b")
            fun_test.simple_assert(lsblk_output, "Listing available volumes")

            # Checking that the above created BLT volume is visible to the end host
            self.nvme_block_device_list = []
            for num in xrange(self.ec_info["num_volumes"]):
                volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n" + str(num+1)
                for volume_name in lsblk_output:
                    match = re.search(volume_pattern, volume_name)
                    if match:
                        self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + str(num+1)
                        self.nvme_block_device_list.append(self.nvme_block_device)
                        self.volume_name = self.nvme_block_device.replace("/dev/", "")
                        fun_test.test_assert_expected(expected=self.volume_name,
                                                      actual=lsblk_output[volume_name]["name"],
                                                      message="{} device available".format(self.volume_name))
                        break
                else:
                    fun_test.test_assert(False, "{} device available".format(self.volume_name))
                fun_test.log("NVMe Block Device/s: {}".format(self.nvme_block_device_list))

            fun_test.shared_variables["nvme_block_device"] = self.nvme_block_device
            fun_test.shared_variables["volume_name"] = self.volume_name
            fun_test.shared_variables["ec"]["nvme_connect"] = True

            self.fio_filename = ":".join(self.nvme_block_device_list)
            fun_test.shared_variables["self.fio_filename"] = self.fio_filename

        # Executing the FIO command to fill the volume to it's capacity
        if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:

            fun_test.log("Executing the FIO command to perform sequential write to volume")
            fio_output = self.end_host.pcie_fio(filename=self.fio_filename, cpus_allowed=self.numa_cpus,
                                                **self.warm_up_fio_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Pre-populating the volume")

            fun_test.shared_variables["ec"]["warmup_io_completed"] = True"""

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        # Going to run the FIO test for the block size and iodepth combo listed in fio_numjobs_iodepth
        fio_result = {}
        fio_output = {}

        for k, v in self.fio_cmd_args.iteritems():
            if k == "bs":
                fio_block_size = self.fio_cmd_args["bs"]
                break
            if k == "bssplit":
                fio_block_size = "Mixed"
                break

        for combo in self.fio_numjobs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}

            fio_num_jobs = combo.split(',')[0].strip('() ')
            fio_iodepth = combo.split(',')[1].strip('() ')

            for mode in self.fio_modes:
                fio_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_num_jobs)
                size = self.ec_info["capacity"] / (1024 ** 3)
                row_data_dict["size"] = str(size) + "G"

                fun_test.sleep("Waiting in between iterations", self.iter_interval)
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(mode, fio_block_size, fio_iodepth, fio_num_jobs))
                fio_job_name = "{}_iodepth_{}_f1_{}_vol_1".format(self.fio_job_name,
                                                                  str(int(fio_iodepth) * int(fio_num_jobs)),
                                                                  self.num_f1s)
                fio_output[combo][mode] = {}
                for host_ip in self.nvme_block_device_list:
                    fio_filename = ":".join(self.nvme_block_device_list[host_ip])
                    fio_output[combo][mode] = self.host_handles[host_ip].pcie_fio(filename=fio_filename, rw=mode,
                                                                                  numjobs=fio_num_jobs,
                                                                                  iodepth=fio_iodepth,
                                                                                  name=fio_job_name,
                                                                                  cpus_allowed=self.host_numa_cpus[
                                                                                      host_ip],
                                                                                  **self.fio_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output[combo][mode]))
                    fun_test.test_assert(fio_output[combo][mode],
                                         "FIO {} test with the Block Size {} IO depth {} and Numjobs {}"
                                         .format(mode, fio_block_size, fio_iodepth, fio_num_jobs))

                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value))
                        row_data_dict[op + field] = fio_output[combo][mode][op][field]

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                row_data_dict["fio_job_name"] = fio_job_name

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                # TODO: enable before merging to master
                # post_results("Inspur Performance Test", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for combo in self.fio_numjobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class RandReadWrite8kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1: 8k data block random read/write IOPS performance of Multiple "
                                      "EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RandReadWrite8kBlocks, self).setup()

    def run(self):
        super(RandReadWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocks, self).cleanup()


class SequentialReadWrite1024kBlocks(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.11.2: 1024k data block sequential write IOPS performance"
                                      "of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 1024k transfer size Sequential write IOPS
        """)

    def setup(self):
        super(SequentialReadWrite1024kBlocks, self).setup()

    def run(self):
        super(SequentialReadWrite1024kBlocks, self).run()

    def cleanup(self):
        super(SequentialReadWrite1024kBlocks, self).cleanup()


class MixedRandReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Inspur TC 8.11.3: Integrated model read/write IOPS performance of Multiple "
                                      "EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for Integrated Model read/write IOPS
        """)

    def setup(self):
        super(MixedRandReadWriteIOPS, self).setup()

    def run(self):
        super(MixedRandReadWriteIOPS, self).run()

    def cleanup(self):
        super(MixedRandReadWriteIOPS, self).cleanup()


class OLTPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Inspur TC 8.11.4: OLTP Model read/read IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLTP model read/write IOPS
        """)

    def setup(self):
        super(OLTPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLTPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLTPModelReadWriteIOPS, self).cleanup()


class OLAPModelReadWriteIOPS(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Inspur TC 8.11.5: OLAP Model read/write IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLAP model Random read/write IOPS
        """)

    def setup(self):
        super(OLAPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLAPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLAPModelReadWriteIOPS, self).cleanup()


class RandReadWrite8kBlocksLatencyTest(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Inspur TC 8.11.6: 8k data block random read/write latency test of Multiple "
                                      "EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write latency
        """)

    def setup(self):
        super(RandReadWrite8kBlocksLatencyTest, self).setup()

    def run(self):
        super(RandReadWrite8kBlocksLatencyTest, self).run()

    def cleanup(self):
        super(RandReadWrite8kBlocksLatencyTest, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(RandReadWrite8kBlocks())
    # ecscript.add_test_case(MixedRandReadWriteIOPS())
    # ecscript.add_test_case(SequentialReadWrite1024kBlocks())
    # ecscript.add_test_case(OLTPModelReadWriteIOPS())
    # ecscript.add_test_case(OLAPModelReadWriteIOPS())
    # ecscript.add_test_case(RandReadWrite8kBlocksLatencyTest())
    ecscript.run()
