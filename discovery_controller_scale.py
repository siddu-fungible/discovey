from lib.system.fun_test import *
from lib.system import utils
from lib.templates.storage.storage_operations_template_old import StorageControllerOperationsTemplate, HostsState

fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *
from swagger_client.rest import ApiException
import string, random
from collections import OrderedDict, Counter


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self, host_obj=None, host_info=None):
        already_deployed = True
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        fun_test.shared_variables["fs_obj_list"] = fs_obj_list
        # fun_test.shared_variables["f1_index"] = self.f1_index
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template

        # NVMe driver check code
        for host_obj in self.topology.get_available_host_instances():
            host_handle = host_obj.get_instance()
            command_result = host_handle.sudo_command("lsmod | grep -w nvme")
            if "nvme" in command_result:
                fun_test.log("nvme driver is loaded")
            else:
                fun_test.log("Loading nvme")
                host_handle.sudo_command.modprobe("nvme")
                host_handle.sudo_command.modprobe("nvme_core")
            command_result = host_handle.sudo_command("lsmod |grep -w nvme_tcp")
            if "nvme_tcp" in command_result:
                fun_test.log("nvme_tcp driver is loaded")
            else:
                fun_test.log("Loading nvme_tcp")
                host_handle.sudo_command.modprobe("nvme_tcp")
                host_handle.sudo_command.modprobe("nvme_fabrics")

    def cleanup(self):
        self.topology.cleanup()
        # pass


class GenericCreateAttachDetachDelete(FunTestCase):

    def __init__(self, **kwargs):
        super(GenericCreateAttachDetachDelete, self).__init__(**kwargs)
        self.api_logging_level = None
        self.NVME_HOST_MODULES = ["nvme_core", "nvme", "nvme_fabrics", "nvme_tcp"]

    def setup(self):

        testcase = self.__class__.__name__

        self.topology = fun_test.shared_variables["topology"]
        self.blt_template = fun_test.shared_variables["storage_controller_template"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        tc_config = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        tc_config = {}
        tc_config = utils.parse_file_to_json(benchmark_file)

        if testcase not in tc_config or not tc_config[testcase]:
            tc_config = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in tc_config[testcase].iteritems():
            setattr(self, k, v)

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "blt_per_host" in job_inputs:
            self.blt_per_host = job_inputs["blt_per_host"]
        if "num_hosts" in job_inputs:
            self.num_host = job_inputs["num_hosts"]
        if "test_iteration_count" in job_inputs:
            self.test_iteration_count = job_inputs["test_iteration_count"]

        fun_test.shared_variables["blt_per_host"] = self.blt_per_host
        self.vol_type = VolumeTypes().LOCAL_THIN
        self.hosts = self.topology.get_available_host_instances()

    def run(self):
        global count
        self.blt_count = self.blt_per_host
        for count in range(self.test_iteration_count):
            self.vol_uuid_list = []
            for i in range(self.blt_count):
                suffix = utils.generate_uuid(length=4)
                body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(i),
                                                                   vol_type=self.vol_type,
                                                                   capacity=self.capacity, compression_effort=False,
                                                                   encrypt=self.encrypt, data_protection={})
                vol_uuid = self.blt_template.create_volume(self.fs_obj_list, body_volume_intent_create)
                fun_test.test_assert(expression=vol_uuid and vol_uuid[0], message="Create Volume{} Successful with "
                                                                                  "uuid {}".format(i + 1, vol_uuid[0]))
                self.vol_uuid_list.append(vol_uuid[0])

            # Do a nvme connect-all from the host
            for index, fs_obj in enumerate(self.fs_obj_list):
                self.attach_vol_result = self.blt_template.attach_volume(host_obj=self.hosts, fs_obj=fs_obj,
                                                                         volume_uuid=self.vol_uuid_list[index],
                                                                         validate_nvme_connect=True, discover=True,
                                                                         raw_api_call=True)
                fun_test.test_assert(expression=self.attach_vol_result, message="Attach Volume Successful")

        time.sleep(120)
        self.cleanupio()
        fun_test.test_assert(expression=True, message="Test completed {} Iteration".format(count + 1))

    def cleanupio(self):
        self.hosts_state_object = HostsState()
        for host_obj in self.topology.get_available_host_instances():
            host_handle = host_obj.get_instance()
            host_handle.sudo_command("killall fio")
            fun_test.add_checkpoint(checkpoint="Kill any running FIO processes")
            disconnected_nvme_devices = []
            host_namespaces = self.hosts_state_object.get_host_nvme_namespaces(hostname=host_obj.name)
            for nvme_namespace in self.hosts_state_object.get_host_nvme_namespaces(hostname=host_obj.name):
                nvme_device = self._get_nvme_device_namespace(namespace=nvme_namespace)
                if nvme_device and nvme_device not in disconnected_nvme_devices:
                    host_handle.nvme_disconnect(device=nvme_device)
                    fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                            format(nvme_device, host_obj.name))
                    disconnected_nvme_devices.append(nvme_device)

            for driver in self.NVME_HOST_MODULES[::-1]:
                host_handle.sudo_command("rmmod {}".format(driver))
            fun_test.add_checkpoint(checkpoint="Unload all NVMe drivers")

            for driver in self.NVME_HOST_MODULES:
                host_handle.modprobe(driver)
                fun_test.add_checkpoint(checkpoint="Reload all NVMe drivers")

        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                for port in get_volume_result["data"][volume]["ports"]:
                    detach_volume = None
                    try:
                        detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    except ApiException as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    detach_result = False
                    if detach_volume:
                        detach_result = detach_volume.status
                    fun_test.add_checkpoint(expected=True, actual=detach_result,
                                            checkpoint="Detach Volume {} from host with host_nqn {}".format(
                                                volume,
                                                get_volume_result["data"][volume]['ports'][port]['host_nqn']))
                delete_volume = None
                try:
                    delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                except ApiException as e:
                    fun_test.critical("Exception while detaching volume: {}\n".format(e))
                except Exception as e:
                    fun_test.critical("Exception while detaching volume: {}\n".format(e))
                delete_volume_result = False
                if delete_volume:
                    delete_volume_result = delete_volume.status
                fun_test.add_checkpoint(expected=True, actual=delete_volume_result,
                                        checkpoint="Delete Volume {}".format(volume))
    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.blt_template

    def _get_nvme_device_namespace(self, namespace):
        result = None
        if "/dev/" in namespace:
            nvme_device = namespace[:-2].split('/dev/')[1]
        else:
            nvme_device = namespace[:-2]
        if nvme_device.split("nvme")[0] == '' and nvme_device.split("nvme")[1].isdigit():
            result = nvme_device
        return result


class ConnectAllMaxVolumeFromOneHost(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create max volumes",
                              steps='''
                                    1. Create 1000 volumes
                                    2. Do a connect-all to all 1000 volumes
                                    3. Check whether discovery controller does not crash
                              ''')

        def setup(self):
            super(ConnectAllMaxVolumeFromOneHost, self).setup()

        def run(self):
            super(ConnectAllMaxVolumeFromOneHost, self).run()

        def cleanup(self):
            super(ConnectAllMaxVolumeFromOneHost, self).cleanup()


class ConnectAllMaxHosts(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Create max volumes",
                              steps='''
                                    1. Create 1000 volumes and assign to differnet host nqn's
                                    2. Do a connect-all to all 1000 volumes from different host nqn's at the same time
                                    3. Check whether discovery controller does not crash
                                    Tip: Send blt_per_host = 1  as job_inputs in submission
                              ''')

        def setup(self):
            super(ConnectAllMaxHosts, self).setup()

        def run(self):
            super(ConnectAllMaxHosts, self).run()

        def cleanup(self):
            super(ConnectAllMaxHosts, self).cleanup()


class ConnectAllContinuous(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Create 20 volumes. Do a continous connect-all from the host with volume ATTACH/DETACH operations",
                              steps='''
                                    1. Create 20 volumes and ATTACH to a single host
                                    2. In Thread1 : Do a continuous connect-all to all volumes from single host
                                    3. In Thread2 : Create new volume and attach to the host every second
                                    4. In Thread3:  Detach a volume from the host every 2 seconds
                                    5. Check whether discovery controller does not crash
                                    6. Test runtime should be configurable: Min 10 mins
                                    Tip: Script involves threading, Look into storage/raw_volume_sanity.py. Discuss with Yajat incase of doubts.
                              ''')

        def setup(self):
            super(ConnectAllContinuous, self).setup()

        def run(self):
            super(ConnectAllContinuous, self).run()

        def cleanup(self):
            super(ConnectAllContinuous, self).cleanup()


class ConnectAllContinuousMultiHost(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Create 30 volumes. Do a continous connect-all from multiple hosts with volume ATTACH/DETACH operations",
                              steps='''
                                    1. Create 10 volumes and ATTACH to a host1
                                    2. Create 10 more volumes and ATTACH to host2
                                    3. Create 10 more volumes and ATTACH to host3
                                    2. In Thread1 : Do a continuous connect-all to all volumes from host1
                                    3. In Thread2 : Do a continuous connect-all to all volumes from host2
                                    4. In Thread3 : Do a continuous connect-all to all volumes from host3
                                    5. In Thread4 : Do ATTACH/DETACH of volumes in host1
                                    4. In Thread5:  Create new volumes. Do not Attach to any host 
                                       Validate whether the new volumes does not get listed in discovery log
                                    5. Check whether discovery controller does not crash
                                    6. Test runtime should be configurable: Min 10 mins
                                    Tip: Script involves threading, Look into storage/raw_volume_sanity.py. Discuss with Yajat incase of doubts.
                              ''')

        def setup(self):
            super(ConnectAllContinuous, self).setup()

        def run(self):
            super(ConnectAllContinuous, self).run()

        def cleanup(self):
            super(ConnectAllContinuous, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(ConnectAllMaxVolumeFromOneHost())
    # TO be done
    # setup_bringup.add_test_case(ConnectAllMaxHosts())
    # setup_bringup.add_test_case(ConnectAllContinuous())
    # setup_bringup.add_test_case(ConnectAllContinuousMultiHost())

    setup_bringup.run()
