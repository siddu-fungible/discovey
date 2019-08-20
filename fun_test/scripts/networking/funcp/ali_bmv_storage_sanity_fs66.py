from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.host.storage_controller import StorageController
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/ali_bmv_storage_sanity.json')

    def cleanup(self):
        fun_test.shared_variables["topology"].cleanup()
        # funcp_obj.cleanup_funcp()
        # for server in servers_mode:
        #     critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")


class BringupSetup(FunTestCase):
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
                                                      '/ali_bmv_storage_sanity.json')

    def run(self):
        # Last working parameter:
        # --environment={\"test_bed_type\":\"fs-alibaba_demo\",\"tftp_image_path\":\"divya_funos-f1.stripped_june5.gz\"}

        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=2 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=2 workload=storage"

        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.cleanup_funcp()
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        servers_list = []

        for server in servers_mode:
            print server
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)
        print(servers_list)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Bringup FunCP
        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        # Assign MPG IPs from dhcp
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

        # funcp_obj.fetch_mpg_ips() #Only if not running the full script"""

    def cleanup(self):
        pass


class NicEmulation(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup PCIe Connceted Hosts and test traffic",
                              steps="""
                              1. Reboot connected hosts
                              2. Verify for PICe Link
                              3. Install Funeth Driver
                              4. Configure HU interface
                              5. Configure FunCP according to HU interfaces
                              6. Add routes on FunCP Container
                              7. Ping NU host from HU host
                              8. Do netperf
                              """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/ali_bmv_storage_sanity.json')

    def run(self):
        # execute abstract Configs
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]

        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

        # Add static routes on Containers
        funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
        fun_test.sleep(message="Waiting before ping tests", seconds=10)

        # Ping QFX from both F1s
        # ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        # for container in ping_dict:
        #     funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

        # Ping vlan to vlan
        funcp_obj.test_cc_pings_fs()
        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])
        # install drivers on PCIE connected servers
        tb_file = str(fs_name)
        if fs_name == "fs-alibaba-demo":
            tb_file = "FS45"
        tb_config_obj = tb_configs.TBConfigs(tb_file)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, sriov=4, num_queues=1)

        # get ethtool output
        get_ethtool_on_hu_host(funeth_obj)

        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host])
        fun_test.sleep(message="Wait for host to check ping again", seconds=30)
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host], strict=True)
            
    def cleanup(self):
        pass


class StorageConfiguration(FunTestCase):
    def describe(self):
        self.set_test_details(id=5, summary="Storage tests", steps="1. Configure volumes")

    def setup(self, config):
        testcase = self.__class__.__name__
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_parent_directory() + '/ali_bmv_storage_sanity.json'
        # fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        self.server_key = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/ali_bmv_storage_sanity.json')
        self.storage_config = self.server_key[config]
        server = []
        server = self.storage_config['server']
        self.host = Linux(host_ip=server[0], ssh_username=self.uname, ssh_password=self.pwd)

        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        """for service in udev_services:
            service_status = self.host.systemctl(service_name=service, action="stop")"""
        # fun_test.test_assert(service_status, "Stopping {} service".format(service))

    def run(self):
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0

        # self.storage_controller_0 = StorageController(target_ip="10.1.105.165", target_port=40220)
        # self.storage_controller_1 = StorageController(target_ip="10.1.105.165", target_port=40221)
        # command_result = self.storage_controller_0.poke(props_tree=["params/syslog/level", 2], legacy=False)
        # fun_test.test_assert(command_result["status"], "Setting syslog level to 2")
        # command_result = self.storage_controller_1.poke(props_tree=["params/syslog/level", 2], legacy=False)
        # fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False

        # Create namespace
        # self.storage_controller = fun_test.shared_variables["storage_controller"]
        print("\n")
        print("====================")
        print("|Creating namespace|")
        print("====================")
        print("\n")

        self.total_num_ns = self.storage_config['num_namespace']
        self.thin_uuid = {}
        if self.vol_type == "RDS":
            for i in range(1, self.total_num_ns + 1, 1):
                self.thin_uuid[i] = utils.generate_uuid()
                command_result = {}
                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                       capacity=self.capacity,
                                                                       block_size=self.block_size,
                                                                       uuid=self.thin_uuid[i],
                                                                       name="rds-block1",
                                                                       remote_nsid=1,
                                                                       remote_ip=self.remote_ip_rds,
                                                                       port=self.port,
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                     format(self.thin_uuid[i]))
                fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
        else:

            for i in range(1, self.total_num_ns + 1, 1):
                self.thin_uuid[i] = utils.generate_uuid()
                command_result = {}
                command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                       capacity=self.capacity,
                                                                       block_size=self.block_size,
                                                                       uuid=self.thin_uuid[i],
                                                                       name="thin_blk" + str(i),
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                     format(self.thin_uuid[i]))
                fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} creation with capacity {}".
                                         format(i, self.capacity))

        # Create the controller
        # PCI controller creation
        if self.vol_type != "RDS":
            print("\n")
            print("===================")
            print("Creating Controller")
            print("===================\n")

            #self.num_ctrl = self.num_vf + 1
            self.num_ctrl = 2
            if self.transport == "PCI":
                self.ctrlr_uuid = {}
                if self.dpu == 0:
                    self.huid = []
                    self.huid = self.f0_huids
                else:
                    self.huid = self.f1_huids
                x = 0
                for i in range(1, self.num_ctrl + 1, 1):
                    self.ctrlr_uuid[i] = utils.generate_uuid()
                    #self.f0_fnid += 1

                    command_result = {}
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                               transport=self.transport,
                                                                               fnid=self.fnid,
                                                                               ctlid=self.ctlid,
                                                                               huid=self.huid[x],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.ctrlr_uuid[i]))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
                    x +=1

            # RDS controller

            else:
                print("\n")
                print("===================")
                print("Creating Controller")
                print("===================\n")

                for i in range(1, self.num_ctrl + 1, 1):
                    self.rds_ctrlr_uuid = {}
                    self.rds_ctrlr_uuid[i] = utils.generate_uuid()
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.rds_ctrlr_uuid[i],
                                                                               transport=self.transport,
                                                                               remote_ip=self.remote_ip,
                                                                               nqn="nqn-1",
                                                                               port=self.port,
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.rds_ctrlr_uuid[i]))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["blt"]["rds_ctrlr_uuid"] = self.rds_ctrlr_uuid[i]
        print("\n")
        print("===================")
        print("Attaching namespace")
        print("===================\n")

        # Attach namespace
        if self.num_vf > 0:
            self.count = self.num_namespace * self.num_vf
        else:
            self.count = self.num_namespace / 2

        self.ctlid_count = 1

        if self.ctrl_type == "RDS":
            self.nsid = 1
            # cur_ctrlid = {}
            cur_ctrlid = fun_test.shared_variables["blt"]["rds_ctrlr_uuid"]
            # cur_ctrlid = fun_test.shared_variables["rds_ctrlr_uuid"]
            for i in range(1, self.num_namespace + 1, 1):
                cur_uuid = self.thin_uuid[i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=cur_ctrlid,
                                                                                     vol_uuid=cur_uuid,
                                                                                     ns_id=self.nsid,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                     format(self.thin_uuid[i], cur_ctrlid))
                if i == self.count:
                    # self.num_namespace = self.num_namespace
                    self.nsid = 1
                    self.ctlid_count += 1
                else:
                    pass
        else:

            if self.vol_attach_type == "remote":
                self.nsid = 2
            else:
                self.nsid = 1

            self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]

            ctrl_num = 1
            for i in range(1, self.num_namespace + 1, 1):
                cur_uuid = self.thin_uuid[i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid[ctrl_num],
                                                                                     vol_uuid=cur_uuid,
                                                                                     ns_id=self.nsid,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                     format(self.thin_uuid[i], self.ctrlr_uuid[ctrl_num]))
                self.nsid +=1
                if i == self.count:
                    # self.num_namespace = self.num_namespace
                    self.nsid = 1
                    ctrl_num += 1
                    self.ctlid_count += 1
                else:
                    pass

    def runio(self, device):
        print("\n")
        print("============================================")
        print("F1 volume stats at the beginning of the test")
        print("============================================\n")

        initial_volume_stats = {}
        for i in range(1, self.num_namespace + 1, 1):
            command_result = {}
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)
            """fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT")
            initial_volume_stats[i] = command_result["data"]
            fun_test.log("Volume Stats at the beginning of the test:")
            fun_test.log(initial_volume_stats[i])"""

        for i in self.storage_config['mode']:
            fio_result = self.host.pcie_fio(filename=device, rw=i,
                                            numjobs=self.num_jobs,
                                            iodepth=self.iodepth,
                                            name="fio_" + str(i), fill_device=1, prio=0, direct=1)

        fun_test.log("======================================")
        fun_test.log("F1 volume stats at the end of the test")
        fun_test.log("======================================")

        for i in range(1, self.num_namespace + 1, 1):
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)

        print("\n")
        print("====================================")
        print("iostat on host at the end of the test")
        print("====================================\n")

        self.host.command(command="sudo iostat")

    def runio_remote(self, device):

        print("\n")
        print("============================================")
        print("F1 volume stats at the beginning of the test")
        print("============================================\n")

        initial_volume_stats = {}
        for i in range(1, self.num_namespace + 1, 1):
            command_result = {}
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_RDS",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)
            """fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT")
            initial_volume_stats[i] = command_result["data"]
            fun_test.log("Volume Stats at the beginning of the test:")
            fun_test.log(initial_volume_stats[i])"""

        for i in self.storage_config['mode']:
            fio_result = self.host.pcie_fio(filename=device, rw=i,
                                            numjobs=self.num_jobs,
                                            iodepth=self.iodepth,
                                            name="fio_" + str(i), fill_device=1, prio=0, direct=1)

        print("\n")
        print("======================================")
        print("F1 volume stats at the end of the test")
        print("======================================\n")

        for i in range(1, self.num_namespace + 1, 1):
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_RDS",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)

        print("\n")
        print("=====================================")
        print("iostat on host at the end of the test")
        print("========-============================\n")

        self.host.command(command="sudo iostat")

    def cleanup(self):
        pass


class LocalSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Run fio traffic on locally attached SSD",
                              steps="""
                                      1. Create BLT volume
                                      2. Create PCI controller
                                      3. Attach volume to the controller
                                      4. Check if nvme device is present on host
                                      5. Run fio write
                                      6. Run fio read
                                      """)

    def setup(self):
        config = "LocalSSDTest"
        super(LocalSSDTest, self).setup(config)

    def run(self):
        self.vol_type = "PCI"
        self.ctrl_type = "PCI"
        self.vol_attach_type = "local"
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        self.dpu = 0
        super(LocalSSDTest, self).run()
        server = self.storage_config['server']
        i = 0
        for host in server:
            self.host = Linux(host_ip=server[i], ssh_username=self.uname, ssh_password=self.pwd)
            self.host.command("sudo nvme list")
            device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
            fun_test.test_assert(device, message="nvme device visible on host")
            i += 1

        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p1)
        self.dpu = 1
        super(LocalSSDTest, self).run()
        server = self.storage_config['server_f1']
        i = 0
        for host in server:
            self.host = Linux(host_ip=server[i], ssh_username=self.uname, ssh_password=self.pwd)
            self.host.command("sudo nvme list")
            device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
            fun_test.test_assert(device, message="nvme device visible on host")
            i += 1
        """
        def runfio(arg1, device):
            for rw_mode in self.mode:
                fio_result = arg1.pcie_fio(filename=device, rw=rw_mode,
                                           numjobs=self.num_jobs,
                                           iodepth=self.iodepth,
                                           name="fio_" + str(rw_mode),
                                           runtime=1800,
                                           prio=0,
                                           direct=1,
                                           timeout=1900)
                arg1.disconnect()
        """
        # TODO : Seeing lot of memory consumed(32G) on server with 8 disk & 4 IOdepth on host connected to F1_1
        # retimer=0 need to revisit it using below way of running test.
        def runfio(arg1, device):
            for rw_mode in self.mode:
                job_file = "/home/localadmin/mks/fio_{}_jf.txt".format(rw_mode)
                result = arg1.sudo_command("fio {}".format(job_file), timeout=3000)
                if "bad bits" in result.lower() or "verify failed" in result.lower():
                    fun_test.critical(False, "Data verification failed for {} test".format(rw_mode))

        for iter in range(1, 3):
            threads_list = []
            hosts = self.storage_config['io_servers']
            print "=========================="
            print "ITERATION " + str(iter)
            print "=========================="
            for servers in hosts:
                self.host = Linux(host_ip=servers, ssh_username=self.uname, ssh_password=self.pwd)
                device = self.host.command("sudo nvme list -o normal | awk -F ' ' '{print $1}' | grep -i nvme0").\
                    replace("\r", '')
                self.host.sudo_command("sync && echo 3 > /proc/sys/vm/drop_caches")
                device_list = device.replace("\n", ":").rstrip(":")
                thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=runfio,
                                                          arg1=self.host, device=device_list)
                fun_test.sleep("Threadzz started", 2)
                threads_list.append(thread_id)

            fun_test.sleep("Sleeping between thread join...", seconds=10)
            for thread_id in threads_list:
                fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

        # self.storage_controller.disconnect()

    def cleanup(self):
        pass


class RemoteSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Run fio traffic on remotely attached SSD",
                              steps="""
                                              1. Assign IP to remote F1
                                              2. Create BLT volume
                                              3. Create RDS controller
                                              4. Attach volume to RDS controller on remote F1
                                              5. Assign IP to local F1
                                              6. Create RDS volume pointing to the BLT configured on remote F1
                                              7. Attach volume to the previously configured PCI conytroller 
                                              8. Check if nvme device is present on host
                                              9. Run fio write
                                              7. Run fio read
                                              """)

    def setup(self):
        config = "RemoteSSDTest"
        super(RemoteSSDTest, self).setup(config)

    def run(self):
        self.vol_type = "PCI"
        self.ctrl_type = "RDS"
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p1)
        command_result = self.storage_controller.ip_cfg(ip=self.ip, port=self.port)
        fun_test.log(command_result)
        super(RemoteSSDTest, self).run()
        fun_test.sleep(message="delay before configuring f1_0")
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        command_result = self.storage_controller.ip_cfg(ip=self.remote_ip, port=self.port)
        fun_test.log(command_result)
        self.vol_type = "RDS"
        self.ctrl_type = "PCI"
        self.vol_attach_type = "remote"
        super(RemoteSSDTest, self).run()
        self.host.command("sudo nvme list")
        device = self.host.command("sudo nvme list | grep nvme | sed -n 2p | awk {'print $1'}").strip()
        fun_test.test_assert(device, message="nvme device visible on host")
        super(RemoteSSDTest, self).runio_remote(device)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(LocalSSDTest())

#   ts.add_test_case(RemoteSSDTest())
    # T1 : NIC emulation : ifconfig, Ethtool - move Host configs here, do a ping, netperf, tcpdump
    # T2 : Local SSD from FIO
    # T3 : Remote SSD FIO
    ts.run()
