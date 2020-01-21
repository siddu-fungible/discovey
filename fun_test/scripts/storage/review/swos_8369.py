from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict, Counter
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.host.linux import Linux
from threading import Lock
from lib.templates.storage.storage_controller_api import *



class StripeVolumeLevelScript(FunTestScript):
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
            self.syslog = "default"
            self.command_timeout = 5
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        # Declaring default values if not defined in config files
        if not hasattr(self, "dut_start_index"):
            self.dut_start_index = 0
        if not hasattr(self, "host_start_index"):
            self.host_start_index = 0
        if not hasattr(self, "update_workspace"):
            self.update_workspace = False
        if not hasattr(self, "update_deploy_script"):
            self.update_deploy_script = False

        # Using Parameters passed during execution, this will override global and config parameters
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = True
        if "f1_in_use" in job_inputs:
            self.f1_in_use = job_inputs["f1_in_use"]
        if "syslog" in job_inputs:
            self.syslog = job_inputs["syslog"]

        # Deploying of DUTs
        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
        fun_test.shared_variables["csi_cache_miss_enabled"] = self.csi_cache_miss_enabled

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            fun_test.shared_variables["perf_listener_host_name"] = self.perf_listener_host_name
            fun_test.shared_variables["perf_listener_ip"] = self.perf_listener_ip

        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            # Ensure all hosts are up after reboot
            fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                 message="Ensure Host {} is reachable after reboot".format(host_name))

            # TODO: enable after mpstat check is added
            """
            # Check and install systat package
            install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
            fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
            """
            # Ensure required modules are loaded on host server, if not load it
            for module in self.load_modules:
                module_check = host_handle.lsmod(module)
                if not module_check:
                    host_handle.modprobe(module)
                    module_check = host_handle.lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        # Ensuring connectivity from Host to F1's
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            for index, ip in enumerate(self.f1_ips):
                ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(host_name, self.funcp_spec[0]["container_names"][index], ip))

        # Ensuring perf_host is able to ping F1 IP
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
            csi_perf_host_instance = Linux(host_ip=self.csi_perf_host_obj.spec["host_ip"],
                                           ssh_username=self.csi_perf_host_obj.spec["ssh_username"],
                                           ssh_password=self.csi_perf_host_obj.spec["ssh_password"])
            ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
            fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                 format(self.perf_listener_host_name, self.csi_f1_ip))

    def cleanup(self):
        #come_reboot = False
        pass
        #Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
        '''
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
            pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

            fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                         source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                         source_file_path="/tmp/nvme_connect.pcap", target_file_path=pcap_artifact_file)
            fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                        filename=pcap_artifact_file)
        '''

class StripeVolumeLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        self.sc_lock = Lock()
        self.syslog = fun_test.shared_variables["syslog"]

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

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["attach_transport"] = self.attach_transport
        fun_test.shared_variables["nvme_subsystem"] = self.nvme_subsystem

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "num_volumes" in job_inputs:
            self.volumes = job_inputs["num_volumes"]
        if "vol_size" in job_inputs:
            self.ec_info["capacity"] = job_inputs["vol_size"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            if not isinstance(self.csi_perf_iodepth, list):
                self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.fs = fun_test.shared_variables["fs_obj"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
        self.f1_ips = fun_test.shared_variables["f1_ips"][self.f1_in_use]
        self.host_info = fun_test.shared_variables["host_info"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = len(self.host_info)
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]

    def run(self):
        for volume in range(self.volumes):
            self.vol_name = "stripe_api_" + str(volume + 1)
            self.create_volume_and_verify(name=self.vol_name, capacity=self.capacity, stripe_count=self.stripe_count,
                                          vol_type=self.vol_type, encrypt=self.encrypt,
                                          allow_expansion=self.allow_expansion,
                                          data_protection=self.data_protection,
                                          compression_effort=self.compression_effort)

    def create_volume_and_verify(self, name, capacity, stripe_count, vol_type, encrypt, allow_expansion,
                                 data_protection, compression_effort):
        fun_test.shared_variables["come_obj"] = self.come_obj
        come_ip = self.come_obj[0].host_ip
        #come_ip = come_ip.split(":")[1]

        #sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        sc = StorageControllerApi(api_server_ip=come_ip)
        pool_uuid = sc.get_pool_uuid_by_name()
        response = sc.create_volume(pool_uuid, name, capacity, stripe_count,
                                    vol_type,
                                    encrypt, allow_expansion, data_protection,
                                    compression_effort)
        print(response)
        fun_test.log("Here is the response for create volume " + response['message'])
        if response['message'] == "":
            fun_test.critical(response['error_message'])
            #fun_test.critical(response['message'])
        fun_test.test_assert(response['status'], "volume {} create successful".format(self.vol_name))

        # Get volume details from FS 1600
        res = sc.get_volumes()

        volume_present = False
        self.vol_uuid_dict = {}
        if res['data']:
            for volume in res['data'].keys():
                if res['data'][volume]['name'] == name:
                    volume_present = True
                    self.vol_uuid_dict[name] = str(volume)
                    volume_data = res['data'][volume]
        else:
            fun_test.test_assert(res['data'],
                                 message="There are no volumes on {}".format(fun_test.shared_variables["testbed"]))

        # config checks
        if not compression_effort:
            compress = False
        if volume_present:
            config_success = all([volume_data['capacity'] == capacity,
                                  volume_data['state'] == "Online",
                                  volume_data['encrypt'] == encrypt,
                                  volume_data['compress'] == compress,
                                  volume_data['type'] == vol_type])
            if config_success:
                fun_test.log("Volume created with expected config successfully!")
            else:
                fun_test.test_assert(volume_data,
                                     message="Volume created with config different from expected configuration")
        else:
            fun_test.test_assert(res,
                                 message="There is no volume with name {} on {}".format(name, self.testbed_type))

    def cleanup(self):
        come_ip = self.come_obj[0].host_ip
        #come_ip = come_ip.split(":")[1]
        sc = StorageControllerApi(api_server_ip=come_ip)
        #sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        res = sc.get_volumes()
        if res['data']:
            for volume in res['data'].keys():
                vol_uuid = res['data'][volume]['uuid']
                response = sc.delete_volume(vol_uuid)
                fun_test.test_assert_expected("volume deletion successful", response['message'],
                                              message="Delete volume status")

        else:
            fun_test.log("There are no volumes on {} to delete".format(fun_test.shared_variables["testbed"]))

class VolumeCreation(StripeVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Data integrity check on EC Vol with compression effort=1",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        4. Create 200 stripe volumes
        """)

    def setup(self):
        super(VolumeCreation, self).setup()

    def run(self):
        super(VolumeCreation, self).run()

    def cleanup(self):
        super(VolumeCreation, self).cleanup()




if __name__ == "__main__":
    ecscript = StripeVolumeLevelScript()
    ecscript.add_test_case(VolumeCreation())
    ecscript.run()
