from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.host.linux import *
from lib.templates.security.xts_openssl_template import XtsOpenssl


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        fun_test.shared_variables["xts_ssl"] = True

    def cleanup(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        for host in host_dict["f1_0"]:
            host.disconnect()
        for host in host_dict["f1_1"]:
            host.disconnect()


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
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=6"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=6"

        topology_helper = TopologyHelper()
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup

        if deploy_setup:
            funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
            funcp_obj.cleanup_funcp()
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            servers_list = []

            for server in servers_mode:
                critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
                servers_list.append(server)

            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}}
                                               )
            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

            abstract_json_file0 = fun_test.get_script_parent_directory() + '/' + \
                                  self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
            abstract_json_file1 = fun_test.get_script_parent_directory() + '/' + \
                                  self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]



            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

            # Add static routes on Containers
            funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
            fun_test.sleep(message="Waiting before ping tests", seconds=10)

            # Ping QFX from both F1s
            ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
            for container in ping_dict:
                 funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

            print("F1 config done")

            fs = topology.get_dut_instance(index=0)
            come_obj = fs.get_come()
            fun_test.shared_variables["come_obj"] = come_obj
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("iptables -F")
            come_obj.sudo_command("ip6tables -F")
            come_obj.sudo_command("dmesg -c > /dev/null")

            fun_test.log("Getting host details")
            host_dict = {"f1_0": [], "f1_1": []}
            for i in range(0, 23):
                if i <= 11:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_0"]:
                            host_dict["f1_0"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
                elif i > 11 <= 23:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_1"]:
                            host_dict["f1_1"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
            fun_test.shared_variables["hosts_obj"] = host_dict

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])
        else:
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

        fun_test.log("SETUP Done")

    def cleanup(self):
        pass


class CryptoCore(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        host_dict = fun_test.shared_variables["hosts_obj"]
        self.host_obj = host_dict["f1_0"][0]

        self.qemu = QemuStorageTemplate(host=self.host_obj, dut=1)

        # Stop services on host
        self.qemu.stop_host_services()
        write_size = 4096
        data_size = 8192
        self.blt_block_size = 4096
        self.blt_uuid = utils.generate_uuid()
        self.command_timeout = 5
        self.storage_controller = StorageController(target_ip="fs45-come", target_port=40220)
        self.storage_controller_remote = StorageController(target_ip="fs45-come", target_port=40221)
        num_raw_vol = 1
        num_encrypted_vol = 1
        num_rds_vol = 1
        num_rds_encrypted_vol =1
        self.raw_encryp_uuid = {}
        self.raw_uuid = {}

        self.rds_encryp_uuid_f1_1 = {}
        self.raw_uuid_f1_1 = {}


        self.rds_encryp_uuid = {}
        self.rds_raw_uuid = {}



        if not fun_test.shared_variables["xts_ssl"]:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)
            install_status = self.xts_ssl_template.install_ssl()
            fun_test.test_assert(install_status, "Openssl installation")
            fun_test.shared_variables["xts_ssl"] = True
        else:
            self.xts_ssl_template = XtsOpenssl(self.host_obj)

        # Create a BLT with encryption using 256 bit key
        rds_xts_key = {}
        rds_xts_tweak = {}
        xts_key = utils.generate_key(length=32)
        xts_tweak = utils.generate_key(length=8)
        self.blt_capacity = 10737418240

        print("**********************************")
        print("Creating Local volumes on F1_0 \n")
        print("**********************************")

        # Creating Local volumes
        # Creating encrypted local volumes
        for i in range(1, num_encrypted_vol+1, 1):
            self.raw_encryp_uuid[i] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_block_size,
                                                               name="thin_encrypted_block" + str(i),
                                                               encrypt=True,
                                                               key=xts_key,
                                                               xtweak=xts_tweak,
                                                               uuid=self.raw_encryp_uuid[i],
                                                               command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "BLT creation with encryption with uuid {}".
                               format(self.raw_encryp_uuid))


        # Creating raw local volumes
        for i in range(1, num_raw_vol + 1, 1):
            self.raw_uuid[i] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_block_size,
                                                               name="thin_raw_block" + str(i),
                                                               uuid=self.raw_uuid[i],
                                                               command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "BLT creation with uuid {}".
                               format(self.raw_uuid))

        print("*************************************")
        print("Assigning storage IPs on F1_0 & F1_1")
        print("*************************************\n")

        self.storage_controller_remote.ip_cfg(ip="19.1.1.1", port=4420)
        self.storage_controller.ip_cfg(ip="18.1.1.1", port=4420)

        print("**********************************")
        print("RDS controller on F1_1 ")
        print("**********************************\n")
        # Create RDS controller on F1_1
        self.rds_ctrlr_uuid = utils.generate_uuid()
        command_result = self.storage_controller_remote.create_controller(ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                   transport="RDS",
                                                                   remote_ip="18.1.1.1",
                                                                   nqn="nqn-1",
                                                                   port=4420,
                                                                   command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"],
                               "Creation of RDS controller with uuid {}".format(self.rds_ctrlr_uuid))

        print("**********************************")
        print("Creating volumes on F1_1")
        print("**********************************\n")
        # Creating volumes on F1_1
        # Creating encrypted volumes on F1_1
        for i in range(1, num_rds_encrypted_vol + 1, 1):
            self.rds_encryp_uuid_f1_1[i] = utils.generate_uuid()
            command_result = self.storage_controller_remote.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=self.blt_capacity,
                                                                          block_size=self.blt_block_size,
                                                                          name="thin_encrypted_block" + str(i),
                                                                          encrypt=True,
                                                                          key=xts_key,
                                                                          xtweak=xts_tweak,
                                                                          uuid=self.rds_encryp_uuid_f1_1[i],
                                                                          command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "BLT creation with encryption on F1_1 with uuid {}".
                                   format(self.rds_encryp_uuid_f1_1))

        # Creating raw volumes on F1_1
        for i in range(1, num_rds_vol + 1, 1):
            self.raw_uuid_f1_1[i] = utils.generate_uuid()
            command_result = self.storage_controller_remote.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=self.blt_capacity,
                                                                          block_size=self.blt_block_size,
                                                                          name="thin_raw_block" + str(i),
                                                                          uuid=self.raw_uuid_f1_1[i],
                                                                          command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "BLT creation on F1_1 with uuid {}".
                                   format(self.raw_uuid_f1_1))
        vol_type = "encrypt"
        print("**********************************")
        print("Attaching volumes on F1_1")
        print("**********************************\n")


        # Attach volumes on F1_1
        #num_vol = num_encrypted_vol+num_raw_vol
        for i in range(1, num_encrypted_vol+1, 1):
            if vol_type == "encrypt":
                cur_uuid = self.rds_encryp_uuid_f1_1[i]
            #else:
            #    print("Inside else loop")
            #    cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller_remote.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                             ns_id=i,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to RDS controller")
            if i == num_encrypted_vol:
                vol_type = "non-encrypt"

        nsid = i+1
        for i in range(1, num_raw_vol+1, 1):
            #if vol_type == "encrypt":
            #    cur_uuid = self.rds_encryp_uuid_f1_1[i]
            cur_uuid = self.raw_uuid_f1_1[i]
            #else:
            #    print("Inside else loop")
            #    cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller_remote.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                             ns_id=nsid,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to RDS controller")
            #if i == num_encrypted_vol:
            #    vol_type = "non-encrypt"



        print("**********************************")
        print("Creating RDS volumes on F1_0")
        print("**********************************\n")
        # Creating RDS volumes
        # Creating encrypted RDS volume on F1_0
        for i in range(1, num_rds_encrypted_vol + 1, 1):
            # self.rds_encryp_uuid[i] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                   capacity=self.blt_capacity,
                                                                   block_size=self.blt_block_size,
                                                                   uuid=self.rds_encryp_uuid_f1_1[i],
                                                                   name="rds-block1",
                                                                   remote_nsid=1,
                                                                   remote_ip="19.1.1.1",
                                                                   port=4420,
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                 format(self.rds_encryp_uuid_f1_1))

        # Creating encrypted RDS volume on F1_0

        for i in range(1, num_rds_encrypted_vol + 1, 1):
            # self.rds_encryp_uuid_f1_1[i] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                                   capacity=self.blt_capacity,
                                                                   block_size=self.blt_block_size,
                                                                   uuid=self.raw_uuid_f1_1[i],
                                                                   name="rds-block1",
                                                                   remote_nsid=2,
                                                                   remote_ip="19.1.1.1",
                                                                   port=4420,
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                                 format(self.raw_uuid_f1_1))

        print("**********************************")
        print("Creating PCIe controller on F1_0")
        print("**********************************\n")

        # Create a PCIe controller
        self.controller_uuid = utils.generate_uuid()
        command_result = self.storage_controller.create_controller(ctrlr_uuid=self.controller_uuid,
                                                                   transport="PCI",
                                                                   fnid=2,
                                                                   ctlid=0,
                                                                   huid=2,
                                                                   command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"],
                               "Creation of PCIe controller with uuid {}".format(self.controller_uuid))

        print("**********************************")
        print("Attaching local volumes on F1_0")
        print("**********************************\n")
        #  Attach both local volumes and RDS to PCI controller
        vol_type = "encrypt"
        #num_vol = num_encrypted_vol+num_raw_vol

        for i in range(1, num_encrypted_vol+1, 1):
            if vol_type == "encrypt":
                cur_uuid = self.raw_encryp_uuid[i]
            #else:
            #    cur_uuid = self.raw_uuid[i]
            command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.controller_uuid,
                                                                             ns_id=i,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to PCIe controller")
            if i == num_encrypted_vol:
                vol_type = "non-encrypt"

        nsid = i+1
        for i in range(1, num_encrypted_vol+1, 1):
            #if vol_type == "encrypt":
            #    cur_uuid = self.raw_encryp_uuid[i]
            #else:
            #    cur_uuid = self.raw_uuid[i]
            cur_uuid = self.raw_uuid[i]
            command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.controller_uuid,
                                                                             ns_id=nsid,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to PCIe controller")
            nsid +=1

        print("**********************************")
        print("Attaching RDS volumes on F1_0")
        print("**********************************\n")

        vol_type = "encrypt"
        num_vol = num_encrypted_vol + num_raw_vol
        #nsid = i+1
        #nsid =1
        for i in range(1, num_encrypted_vol+1, 1):
            if vol_type == "encrypt":
                cur_uuid = self.rds_encryp_uuid_f1_1[i]
                print("current uuid is {}".format(cur_uuid))
            #else:
            #    cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                                 ctrlr_uuid=self.controller_uuid,
                                                                                 ns_id=nsid,
                                                                                 command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to PCIe controller")
            nsid += 1

        for i in range(1, num_encrypted_vol+1, 1):
            #if vol_type == "encrypt":
            #    cur_uuid = self.raw_encryp_uuid[i]
            #else:
            #    cur_uuid = self.raw_uuid[i]
            cur_uuid = self.raw_uuid_f1_1[i]
            command_result = self.storage_controller.attach_volume_to_controller(vol_uuid=cur_uuid,
                                                                             ctrlr_uuid=self.controller_uuid,
                                                                             ns_id=nsid,
                                                                             command_duration=self.command_timeout)
            fun_test.simple_assert(command_result["status"], "Attaching vol to PCIe controller")
            nsid +=1

        fun_test.sleep(message="sleeping for 10se", seconds=10)

        print("****************************")
        print("Detach RDS volume from F1_0")
        print("****************************\n")


        command_result = self.storage_controller.detach_volume_from_controller(ns_id=3,
                                                                               ctrlr_uuid=self.controller_uuid,
                                                                               command_duration=self.command_timeout)
        #fun_test.simple_assert(command_result["status"], "Detach BLT with uuid {}".format(self.rds_encryp_uuid[1]))

        fun_test.sleep(message="sleeping for 10se", seconds=10)

        print("****************************")
        print("Detlete RDS volume from F1_0")
        print("****************************\n")

        command_result = self.storage_controller.delete_volume(type="VOL_TYPE_BLK_RDS",
                                                               uuid=self.rds_encryp_uuid_f1_1[1],
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Delete BLT with uuid {}".format(self.blt_uuid))

        fun_test.sleep(message="sleeping for 10se", seconds=10)


        print("****************************")
        print("Detach BLT volume from F1_1")
        print("****************************\n")

        command_result = self.storage_controller_remote.detach_volume_from_controller(ns_id=1,
                                                                               ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                               command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Detach BLT with uuid {}".format(self.rds_encryp_uuid_f1_1))

        fun_test.sleep(message="sleeping for 10se", seconds=10)
        print("************************************")
        print("Mount BLT on F_1 without encryption")
        print("************************************\n")

        command_result = self.storage_controller_remote.mount_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                              capacity=self.blt_capacity,
                                                              block_size=self.blt_block_size,
                                                              name="thin_encrypted_block1",
                                                              uuid=self.rds_encryp_uuid_f1_1[1],
                                                              command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Mount BLT without encryption")

        fun_test.sleep(message="sleeping for 10se", seconds=10)
        print("************************************")
        print("Attach BLT on F_1 ")
        print("************************************\n")

        command_result = self.storage_controller_remote.attach_volume_to_controller(ctrlr_uuid=self.rds_ctrlr_uuid,
                                                                             ns_id=1,
                                                                             vol_uuid=self.rds_encryp_uuid_f1_1[1],
                                                                             command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Attaching BLT without encryption")

        fun_test.sleep(message="sleeping for 10se", seconds=10)
        print("************************************")
        print("Create BLT on F_0 ")
        print("************************************\n")

        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_RDS",
                                                               capacity=self.blt_capacity,
                                                               block_size=self.blt_block_size,
                                                               uuid=self.rds_encryp_uuid_f1_1[1],
                                                               name="rds-block1",
                                                               remote_nsid=1,
                                                               remote_ip="19.1.1.1",
                                                               port=4420,
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Creating volume with uuid {}".
                             format(self.rds_encryp_uuid_f1_1))
        fun_test.sleep(message="sleeping for 10se", seconds=10)
        print("************************************")
        print("Attach RDS on F_0 ")
        print("************************************\n")

        command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.controller_uuid,
                                                                                    ns_id=3,
                                                                                    vol_uuid=self.rds_encryp_uuid_f1_1[1],
                                                                                    command_duration=self.command_timeout)
        fun_test.simple_assert(command_result["status"], "Attaching BLT without encryption")







    def cleanup(self):
        pass


class Key256Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Write & Read on 256bit encrypted BLT using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write4k(CryptoCore):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Write & Read on 512bit encrypted BLT using nvme cli with 4k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key256Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Write & Read on 256bit encrypted BLT using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


class Key512Write8k(CryptoCore):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Write & Read on 512bit encrypted BLT using nvme cli with 8k write_size",
                              steps='''
                              1. Start FunOS and attach host over PCIe.
                              2. Create a BLT with encryption.
                              3. Use NVME write on LBA using data_file.
                              4. Use NVME read on the written block and save in file.
                              5. Compare the input file and the read data file.''')


if __name__ == "__main__":
    crypto_script = ScriptSetup()
    crypto_script.add_test_case(BringupSetup())
    crypto_script.add_test_case(Key256Write4k())
    # crypto_script.add_test_case(Key512Write4k())
    # crypto_script.add_test_case(Key256Write8k())
    # crypto_script.add_test_case(Key512Write8k())

    crypto_script.run()
