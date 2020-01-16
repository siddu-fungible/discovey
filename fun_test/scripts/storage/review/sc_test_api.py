from lib.system.fun_test import *
from lib.templates.storage.storage_controller_api import *
from lib.fun.fs import *
from lib.topology.topology_helper import *
from scripts.storage.storage_helper import *


class StorageControlerTestScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
           1. Deploy the topology. i.e Bring up FS
           2. Make the Linux instance available for the testcase
           """)

    def setup(self):
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        bundle_params = fun_test.get_job_environment_variable("bundle_image_parameters")
        self.version = bundle_params["build_number"]
        self.fs = AssetManager().get_fs_spec(self.testbed_type)
        fun_test.shared_variables["come_ip"] = self.fs['come']['mgmt_ip']

        if self.version == 'latest':
            try:
                output = os.popen("curl http://dochub.fungible.local/doc/jenkins/master/fs1600/latest/bld_props.json")
                output_string = output.read()
                bld_version = re.search('"bldNum": "(\d+)"', output_string)
                target_bld = bld_version.groups(1)[0]
            except Exception as ex:
                fun_test.test_assert(str(ex))
        else:
            target_bld = self.version

        fun_test.shared_variables['target_version'] = target_bld  # later used for verification

        sc = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'])
        current_version = sc.get_version()
        if not current_version:
            fun_test.test_assert(current_version, "Unable to get the current version")

        if current_version == target_bld:
            fun_test.log("Current bundle image version is same as target version, Skipping upgrade and continuing "
                         "with test cases")
        else:
            self.topology_helper = TopologyHelper()
            self.topology = self.topology_helper.deploy()
            fun_test.test_assert(self.topology, "Topology deployed")
            fun_test.sleep("Wait before proceeding to the test cases", seconds=120)

    def cleanup(self):
        pass


class VerifyImageVersion(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Verifying Bundle Image version",
                              steps='''''')

    def setup(self):
        pass

    def run(self):
        sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        current_version = sc.get_version()
        if not current_version:
            fun_test.test_assert(current_version, "Unable to get the current version")
        fun_test.log("Current version on the FS1600 is {}".format(current_version))
        target_version = fun_test.shared_variables['target_version']
        fun_test.test_assert_expected(target_version, current_version, "Bundle image version verification")

    def cleanup(self):
        pass


class CreateRawVolumes(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Create Raw volumes",
                              steps='''''')

    def setup(self):
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_spec(self.testbed_type)
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)

        testcase = self.__class__.__name__

        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

    def run(self):
        for volume in range(self.volumes):
            vol_name = "raw_api_" + str(volume + 1)
            self.create_volume_and_verify(name=vol_name, capacity=self.capacity, stripe_count=self.stripe_count,
                                          vol_type=self.vol_type, encrypt=self.encrypt,
                                          allow_expansion=self.allow_expansion,
                                          data_protection=self.data_protection,
                                          compression_effort=self.compression_effort)

    def create_volume_and_verify(self, name, capacity, stripe_count, vol_type, encrypt, allow_expansion,
                                 data_protection, compression_effort):

        sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        pool_uuid = sc.get_pool_uuid_by_name()
        response = sc.create_volume(pool_uuid, name, capacity, stripe_count,
                                    vol_type,
                                    encrypt, allow_expansion, data_protection,
                                    compression_effort)
        fun_test.log("Here is the response for create volume " + response['message'])
        if response['message'] == "":
            fun_test.critical(response['error_message'])
        fun_test.test_assert_expected("volume create successful", response['message'], "RAW volume creation status")

        # Get volume details from FS 1600
        res = sc.get_volumes()

        volume_present = False
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
        sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        res = sc.get_volumes()
        if res['data']:
            for volume in res['data'].keys():
                vol_uuid=res['data'][volume]['uuid']
                response = sc.delete_volume(vol_uuid)
                fun_test.test_assert_expected("volume deletion successful", response['message'],
                                              message="Delete volume status")

        else:
            fun_test.log("There are no volumes on {} to delete".format(fun_test.shared_variables["testbed"]))


class ConnectAllVolumestoHost(CreateRawVolumes):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Connect Volumes to Host",
                              steps='''''')

    def setup(self):
        super(ConnectAllVolumestoHost, self).setup()
        self.vol_uuid_dict = {}

    def run(self):
        super(ConnectAllVolumestoHost, self).run()
        if self.write_hosts:
            required_hosts_list = self.verify_and_get_required_hosts_list(self.write_hosts + self.read_hosts)
            required_write_hosts_list = required_hosts_list[:self.write_hosts]
            required_read_hosts_list = required_hosts_list[self.write_hosts:(self.read_hosts + 1):]
            sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
            self.pool_uuid = sc.get_pool_uuid_by_name()
            self.volume_uuid_details = self.vol_uuid_dict
            self.attach_volumes_to_host(required_write_hosts_list)
            self.get_host_handles()
            self.initialize_the_hosts()
            self.connect_the_host_to_volumes()
            self.verify_nvme_connect()
            self.disconnect_the_hosts()
            self.destoy_host_handles()

    def verify_and_get_required_hosts_list(self, num_hosts):
        available_hosts_list = []
        try:
            if self.testbed_type == "suite-based":
                self.topology_helper = TopologyHelper()
                available_hosts_list = OrderedDict(self.topology_helper.get_available_hosts())
            else:
                self.fs_hosts_map = utils.parse_file_to_json(SCRIPTS_DIR + "/storage/apple_rev2_fs_hosts_mapping.json")
                available_hosts_list = self.fs_hosts_map[self.testbed_type]["host_info"]
        except Exception as ex:
            fun_test.critical(ex)
        required_hosts_available = True if (len(available_hosts_list) >= num_hosts) else False
        fun_test.log("Expected hosts: {}, Available hosts: {}".format(num_hosts, len(available_hosts_list)))
        fun_test.test_assert(required_hosts_available, "Required hosts available")
        required_hosts_list = available_hosts_list[:num_hosts]
        return required_hosts_list

    def attach_volumes_to_host(self, required_hosts_list):
        self.host_details = {}
        sc = StorageControllerApi(api_server_ip=fun_test.shared_variables["come_ip"])
        for index, host_name in enumerate(required_hosts_list):
            host_interface_ip = self.hosts_asset[host_name]["test_interface_info"]["0"]["ip"].split("/")[0]
            for vol_name, vol_uuid in self.volume_uuid_details.iteritems():
                response = sc.volume_attach_remote(vol_uuid=self.volume_uuid_details[vol_name],
                                                   remote_ip=host_interface_ip)

                fun_test.log("Volume attach response: {}".format(response))
                message = response["message"]
                attach_status = True if message == "Attach Success" else False
                fun_test.test_assert(attach_status, "Attach host: {} to volume: {}".format(host_name, vol_name))
                self.host_details[host_name] = {}
                self.host_details[host_name]["data"] = response["data"]
                self.host_details[host_name]["volume_name"] = vol_name
                self.host_details[host_name]["volume_uuid"] = self.volume_uuid_details[vol_name]

    def get_host_handles(self):
        for host_name in self.host_details:
            host_handle = self.get_host_handle(host_name)
            self.host_details[host_name]["handle"] = host_handle

    def get_host_handle(self, host_name):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        return host_handle

    def initialize_the_hosts(self):
        for host_name, host_info in self.host_details.iteritems():
            module = "nvme"
            host_info["handle"].modprobe(module)
            module = "nvme_tcp"
            host_info["handle"].modprobe(module)

    def connect_the_host_to_volumes(self, retry=3):
        for host_name, host_info in self.host_details.iteritems():
            # Try connecting nvme 3 times with an interval of 10 seconds each try, try 5 times
            for iter in range(retry):
                fun_test.log("Trying to connect to nvme, Iteration no: {} out of {}".format(iter + 1, retry))
                nqn = host_info["data"]["nqn"]
                target_ip = host_info["data"]["ip"]
                remote_ip = host_info["data"]["remote_ip"]
                result = host_info["handle"].nvme_connect(target_ip=target_ip,
                                                          nvme_subsystem=nqn,
                                                          nvme_io_queues=16,
                                                          retries=5,
                                                          timeout=100,
                                                          hostnqn=remote_ip)
                if result:
                    break
                fun_test.sleep("Before next iteration", seconds=10)

            fun_test.test_assert(result,
                                 "Host: {} nqn: {} connected to DataplaneIP: {}".format(host_name, nqn, target_ip))

    def verify_nvme_connect(self):
        for host_name, host_info in self.host_details.iteritems():
            output_lsblk = host_info["handle"].sudo_command("nvme list")
            nsid = host_info["data"]["nsid"]
            lines = output_lsblk.split("\n")
            for line in lines:
                match_nvme_list = re.search(r'(?P<nvme_device>/dev/nvme\w+)\s+(?P<namespace>\d+)\s+(\d+)', line)
                if match_nvme_list:
                    namespace = int(match_nvme_list.group("namespace"))
                    if namespace == nsid:
                        host_info["nvme"] = match_nvme_list.group("nvme_device")
                        fun_test.log("Host: {} is connected by nvme device: {}".format(host_name, host_info["nvme"]))
                        break
            verify_nvme_connect = True if "nvme" in host_info else False
            fun_test.test_assert(verify_nvme_connect, "Host: {} nvme: {} verified NVME connect".format(host_name,
                                                                                                       host_info["nvme"]
                                                                                                       ))

    def disconnect_the_hosts(self, strict=True):
        for host_name, host_info in self.host_details.iteritems():
            output = host_info["handle"].sudo_command("nvme disconnect -n {nqn}".format(nqn=host_info["data"]["nqn"]))
            strict_key = " 1" if strict else ""
            disconnected = True if "disconnected{}".format(strict_key) in output else False
            fun_test.test_assert(disconnected,
                                 "Host: {} disconnected from {}".format(host_name, host_info["data"]["ip"]))

    def destoy_host_handles(self):
        for host_name in self.host_details:
            self.host_details[host_name]["handle"].destroy()

    def cleanup(self):
        super(ConnectAllVolumestoHost, self).cleanup()



if __name__ == "__main__":
    sc_obj = StorageControlerTestScript()
    sc_obj.add_test_case(VerifyImageVersion())
    #sc_obj.add_test_case(CreateRawVolumes())
    sc_obj.add_test_case(ConnectAllVolumestoHost())
    sc_obj.run()
