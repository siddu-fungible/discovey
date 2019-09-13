from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.topology.topology_helper import TopologyHelper


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                              1. Cleanup FunCP
                              2. Remove Funeth from Hosts
                              3. BringUP both F1s
                              4. Reboot COMe
                              5. Reboot Hosts
                              """)

    def setup(self):
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "enable_bgp" in job_inputs:
            enable_bgp = job_inputs["enable_bgp"]
            fun_test.shared_variables["enable_bgp"] = enable_bgp
        else:
            enable_bgp = False
            fun_test.shared_variables["enable_bgp"] = enable_bgp

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        global funcp_obj, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        servers_mode = self.server_key["fs"][fs_name]["hosts"]

        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.cleanup_funcp()

        for server in servers_mode:
            print server
            shut_all_vms(hostname=server)
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host %s " % server)

        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
        # b = topology_helper.get_expanded_topology()


    def cleanup(self):
        # funcp_obj.cleanup_funcp()
        fun_test.shared_variables["topology"].cleanup()
        # pass


class BringupControlPlane(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup Control Plane",
                              steps="""
                                  1. Prepare Docker
                                  2. Setup Docker
                                  3. Assign MPG IPs
                                  4. Execute Abstract Configs
                                  """)


    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')


    def run(self):
        enable_bgp = fun_test.shared_variables["enable_bgp"]
        abstract_key = "abstract_configs"
        if enable_bgp:
            abstract_key = "abstract_configs_bgp"

        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=True), message="Bringup FunCP")
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name][abstract_key]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name][abstract_key]["F1-1"]
        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")
        if not enable_bgp:
            funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])

        ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        for container in ping_dict:
            funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)


    def cleanup(self):
        pass


class CheckPCIeWidth(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Check no of PCIe lanes on HU host",
                              steps="""
                                  1. Login into host
                                  2. lspci -d 1dad:
                                  3. Make sure speed is as expected
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        output = True
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            output &= (result == "1")
        fun_test.test_assert(expression=output, message="Make sure that PCIe links on hosts went up with correct speed")

    def cleanup(self):
        pass


class NicEmulation(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="Setup HU host",
                              steps="""
                                  1. Prepare Docker
                                  2. Setup Docker
                                  3. Assign MPG IPs
                                  4. Execute Abstract Configs
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):

        # install drivers on PCIE connected servers
        if fs_name == "fs-alibaba-demo":

            tb_config_obj = tb_configs.TBConfigs(str(fs_name))
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True, sriov=32, num_queues=8)
            get_ethtool_on_hu_host(funeth_obj)

            tb_config_obj = tb_configs.TBConfigs(str(fs_name)+"2")
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True, sriov=4, num_queues=4)
            get_ethtool_on_hu_host(funeth_obj)

            print("\n=================")
            print ("Enable NVMe VFs:")
            print("=================")
            for server in self.server_key["fs"][fs_name]["vm_config"]:
                critical_log(enable_nvme_vfs
                             (host=server,
                              pcie_vfs_count=self.server_key["fs"][fs_name]["vm_config"][server]["pcie_vfs"]),
                             message="NVMe VFs enabled")

        else:

            tb_config_obj = tb_configs.TBConfigs(str(fs_name))
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True, sriov=4, num_queues=1)
            get_ethtool_on_hu_host(funeth_obj)

    def cleanup(self):
        pass


class TestPings(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test Pings",
                              steps="""
                                  1. Test Pings from docker
                                  2. Test Pings from HU host
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        # funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host], strict=True)

        funcp_obj.test_cc_pings_fs()
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(self.server_key["fs"][fs_name]["fs-name"])
        if not funcp_obj.vlan1_ips:
            funcp_obj._get_vlan1_ips()
        if not funcp_obj.docker_names:
            funcp_obj._get_docker_names()
        fun_test.test_assert(cc_sanity_pings(docker_names=funcp_obj.docker_names, vlan_ips=funcp_obj.vlan1_ips,
                                             fs_spec=fs_spec, ping_count=5000,
                                             nu_hosts=self.server_key["fs"][fs_name]["nu_host_data_ip"],
                                             hu_hosts_0=self.server_key["fs"][fs_name]["hu_host_data_ip_f1_0"],
                                             hu_hosts_1=self.server_key["fs"][fs_name]["hu_host_data_ip_f1_1"]),
                             message="Test pings form CC to HU and CC to NU")

    def cleanup(self):
        pass


class TestScp(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=5,
                              summary="Scp file from HU to NU and Vice Versa",
                              steps="""
                                  1. Scp 100MB file form HU host to NU host
                                  2. Scp 100MB file form NU host to HU host
                                  """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        result = True
        for nu_host in self.server_key["fs"][fs_name]["nu_host"]:
            for hu_host in self.server_key["fs"][fs_name]["hu_host"]:
                nu_ip = self.server_key["fs"][fs_name]["nu_host"][nu_host]
                hu_ip = self.server_key["fs"][fs_name]["hu_host"][hu_host]
                result &= test_scp(source_host=nu_host, dest_host=hu_host, source_data_ip=nu_ip, dest_data_ip=hu_ip)
                result &= test_scp(source_host=hu_host, dest_host=nu_host, source_data_ip=hu_ip, dest_data_ip=nu_ip)

        fun_test.test_assert(expression=result, message="SCP result")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupControlPlane())
    ts.add_test_case(CheckPCIeWidth())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(TestPings())
    ts.add_test_case(TestScp())
    ts.run()
