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

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        pass

    def cleanup(self):
        pass


class BringupSetup(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS-45 with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):

        pass

    def run(self):
        # boot_image_f1_0 = "divya_funos-f1.stripped_june3.gz"
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt syslog=6 --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=3 --mgmt syslog=6 --disable-wu-watchdog"
        fs_name = "fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name)

        funcp_obj.cleanup_funcp()

        server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        servers_mode = server_key["fs"][fs_name]
        servers_list = []

        for server in servers_mode:
            print server
            fun_test.test_assert(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)

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
        funcp_obj.assign_mpg_ips(static=True, f1_1_mpg="10.1.105.172", f1_0_mpg="10.1.105.173")

        # funcp_obj.fetch_mpg_ips() #Only if not running the full script

    def cleanup(self):

        pass


class NicEmulation(FunTestCase):
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

        pass

    def run(self):
        # execute abstract Configs

        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/alibaba_bmv_configs_f1_0.json'
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/alibaba_bmv_configs_f1_1.json'
        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")
        # Add static routes on Containers
        server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        routes = server_key["static_routes"][fs_name]
        funcp_obj.add_routes_on_f1(routes_dict=routes)

        # Ping QFX from both F1s
        funcp_obj.test_cc_pings_remote_fs(dest_ips=["1.1.1.1"], docker_name="F1-0")
        funcp_obj.test_cc_pings_remote_fs(dest_ips=["1.1.2.1"], docker_name="F1-1")

        # Ping vlan to vlan
        funcp_obj.test_cc_pings_fs()

        # install drivers on PCIE connected servers
        tb_config_obj = tb_configs.TBConfigs(str('FS' + fs_name.split('-')[1]))
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False)

        # get ethtool output TODO : IFCONFIG, lspci
        get_ethtool_on_hu_host(funeth_obj)

        # Ping hosts

        test_host_pings(hostnames=servers_list, ips=["18.1.1.2", "30.1.1.2"])

    def cleanup(self):
        pass


class StorageConfiguration(FunTestCase):
    def describe(self):
        self.set_test_details(id=3, summary="Storage tests", steps="1. Configure volumes")

    def setup(self, config):
        testcase = self.__class__.__name__
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_parent_directory() + '/fs_connected_servers.json'
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

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        self.storage_config = self.server_key[config]
        server = self.storage_config['server']
        self.host = Linux(host_ip=server, ssh_username=self.uname, ssh_password=self.pwd)

        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.host.systemctl(service_name=service, action="stop")
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
                                                                       remote_nsid = 1,
                                                                       remote_ip = self.remote_ip_rds,
                                                                       port=self.port,
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                    format(self.thin_uuid))
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
                                     format(self.thin_uuid))
                fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} creation with capacity {}".
                                         format(i, self.capacity))

        # Create the controller
        if self.vol_type != "RDS":
            self.num_ctrl = self.num_vf + 1
            self.ctrlr_uuid = {}
            if self.transport == "PCI":
                for i in range(1, self.num_ctrl + 1, 1):
                    self.ctrlr_uuid[i] = utils.generate_uuid()
                    if i == 2:
                        self.f0_fnid = 40
                    elif i > 2:
                        self.f0_fnid += 1
                    command_result = {}
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                 transport=self.transport,
                                                                                 fnid=self.fnid,
                                                                                 ctlid=self.ctlid,
                                                                                 huid=self.huid,
                                                                                 command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.ctrlr_uuid))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["blt"]["ctrlr_uuid"] = self.ctrlr_uuid
            else:
                for i in range(1, self.num_ctrl + 1, 1):
                    command_result = {}
                    self.ctrlr_uuid[i] = utils.generate_uuid()
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                 transport=self.transport,
                                                                                 remote_ip=self.remote_ip,
                                                                                 nqn="nqn-1",
                                                                                 port=self.port,
                                                                                 command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.ctrlr_uuid))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["blt"]["ctrlr_uuid"] = self.ctrlr_uuid


        # Attach namespace
        if self.vol_type == "RDS":
            self.nsid = 2
        else:
            self.nsid = 1

        if self.num_vf > 0:
            self.count = self.num_namespace * self.num_vf
        else:
            self.count = self.num_namespace

        self.ctlid_count = 1

        for i in range(1, self.count + 1, 1):
            cur_uuid = self.thin_uuid[i]
            print("*************")
            print(self.thin_uuid)
            print(cur_uuid)
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                vol_uuid = cur_uuid,
                                                                                ns_id = self.nsid,
                                                                                command_duration = self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                 format(self.thin_uuid[i], self.ctrlr_uuid))
            if i == self.num_namespace:
                # self.num_namespace = self.num_namespace
                self.nsid = 1
                self.ctlid_count += 1
            else:
                pass

    def runio(self, device):
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

        for i in range(1, self.num_namespace + 1, 1):
            command_result = {}
            print("thin_uuid")
            print(self.thin_uuid)
            print("***********")
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)

        self.host.command(command="sudo iostat")

    def cleanup(self):
        pass


class LocalSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=4,
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
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        super(LocalSSDTest, self).run()
        self.host.command("sudo nvme list")
        device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
        fun_test.test_assert(device, message="nvme device visible on host")
        super(LocalSSDTest, self).runio(device)
        self.storage_controller.disconnect()

    def cleanup(self):
        pass


class RemoteSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=5,
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
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p1)
        command_result = self.storage_controller.ip_cfg(ip=self.ip, port=self.port)
        fun_test.log(command_result)
        super(RemoteSSDTest, self).run()
        fun_test.sleep(message="delay before configuring f1_0")
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        command_result = self.storage_controller.ip_cfg(ip=self.remote_ip, port=self.port)
        fun_test.log(command_result)
        self.vol_type = "RDS"
        super(RemoteSSDTest, self).run()
        self.host.command("sudo nvme list")
        device = self.host.command("sudo nvme list | grep nvme | sed -n 2p | awk {'print $1'}").strip()
        fun_test.test_assert(device, message="nvme device visible on host")
        super(RemoteSSDTest, self).runio(device)

    def cleanup(self):
        pass


class StorageConfiguration(FunTestCase):
    def describe(self):
        self.set_test_details(id=3, summary="Storage tests", steps="1. Configure volumes")

    def setup(self, config):
        testcase = self.__class__.__name__
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_parent_directory() + '/fs_connected_servers.json'
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

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        self.storage_config = self.server_key[config]
        server = self.storage_config['server']
        self.host = Linux(host_ip=server, ssh_username=self.uname, ssh_password=self.pwd)

        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.host.systemctl(service_name=service, action="stop")
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
                                                                       remote_nsid = 1,
                                                                       remote_ip = self.remote_ip_rds,
                                                                       port=self.port,
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                    format(self.thin_uuid))
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
                                     format(self.thin_uuid))
                fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} creation with capacity {}".
                                         format(i, self.capacity))

        # Create the controller
        if self.vol_type != "RDS":
            self.num_ctrl = self.num_vf + 1
            self.ctrlr_uuid = {}
            if self.transport == "PCI":
                for i in range(1, self.num_ctrl + 1, 1):
                    self.ctrlr_uuid[i] = utils.generate_uuid()
                    if i == 2:
                        self.f0_fnid = 40
                    elif i > 2:
                        self.f0_fnid += 1
                    command_result = {}
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                 transport=self.transport,
                                                                                 fnid=self.fnid,
                                                                                 ctlid=self.ctlid,
                                                                                 huid=self.huid,
                                                                                 command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.ctrlr_uuid))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["blt"]["ctrlr_uuid"] = self.ctrlr_uuid
            else:
                for i in range(1, self.num_ctrl + 1, 1):
                    command_result = {}
                    self.ctrlr_uuid[i] = utils.generate_uuid()
                    command_result = self.storage_controller.create_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                 transport=self.transport,
                                                                                 remote_ip=self.remote_ip,
                                                                                 nqn="nqn-1",
                                                                                 port=self.port,
                                                                                 command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Creating controller with uuid {}".
                                         format(self.ctrlr_uuid))
                    fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid
                    fun_test.shared_variables["blt"]["ctrlr_uuid"] = self.ctrlr_uuid


        # Attach namespace
        if self.vol_type == "RDS":
            self.nsid = 2
        else:
            self.nsid = 1

        if self.num_vf > 0:
            self.count = self.num_namespace * self.num_vf
        else:
            self.count = self.num_namespace

        self.ctlid_count = 1

        for i in range(1, self.count + 1, 1):
            cur_uuid = self.thin_uuid[i]
            print("*************")
            print(self.thin_uuid)
            print(cur_uuid)
            command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid[i],
                                                                                vol_uuid = cur_uuid,
                                                                                ns_id = self.nsid,
                                                                                command_duration = self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching volume {} to controller {}".
                                 format(self.thin_uuid[i], self.ctrlr_uuid))
            if i == self.num_namespace:
                # self.num_namespace = self.num_namespace
                self.nsid = 1
                self.ctlid_count += 1
            else:
                pass

    def runio(self, device):
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

        for i in range(1, self.num_namespace + 1, 1):
            command_result = {}
            print("thin_uuid")
            print(self.thin_uuid)
            print("***********")
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)

        self.host.command(command="sudo iostat")

    def cleanup(self):
        pass


class LocalSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=4,
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
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        super(LocalSSDTest, self).run()
        self.host.command("sudo nvme list")
        device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
        fun_test.test_assert(device, message="nvme device visible on host")
        super(LocalSSDTest, self).runio(device)

    def cleanup(self):
        pass


class RemoteSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=5,
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
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p1)
        command_result = self.storage_controller.ip_cfg(ip=self.ip, port=self.port)
        fun_test.log(command_result)
        super(RemoteSSDTest, self).run()
        fun_test.sleep(message="delay before configuring f1_0")
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        command_result = self.storage_controller.ip_cfg(ip=self.remote_ip, port=self.port)
        fun_test.log(command_result)
        self.vol_type = "RDS"
        super(RemoteSSDTest, self).run()
        self.host.command("sudo nvme list")
        device = self.host.command("sudo nvme list | grep nvme | sed -n 2p | awk {'print $1'}").strip()
        fun_test.test_assert(device, message="nvme device visible on host")
        super(RemoteSSDTest, self).runio(device)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(LocalSSDTest())
    ts.add_test_case(RemoteSSDTest())
    # T1 : NIC emulation : ifconfig, Ethtool - move Host configs here, do a ping, netperf, tcpdump
    # T2 : Local SSD from FIO
    # T3 : Remote SSD FIO
    ts.run()
