from lib.system.fun_test import *
from lib.system import utils
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

    def setup(self):
        already_deployed = False
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology


        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol6"
        #already_deployed = True
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
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

        if 0:
            vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                           body_volume_intent_create=body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
            hosts = self.topology.get_available_host_instances()
            for index, fs_obj in enumerate(fs_obj_list):
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                                   volume_uuid=vol_uuid_list[index],
                                                                                   validate_nvme_connect=True,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

                print "Attach volume result is " + str(attach_vol_result)

            self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]
        fun_test.shared_variables["fs_obj_list"] = fs_obj_list
        #fun_test.shared_variables["f1_index"] = self.f1_index
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template


    def cleanup(self):
        self.topology.cleanup()
        #pass


class VerifyProtocol(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run all nvme identify commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run all nvme identify commands
                              ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]
        self.fs_obj = fun_test.shared_variables["fs_obj"]
        self.f1_index = fun_test.shared_variables["f1_index"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]


    def getCtrlId(self,lnx,device):
        op = json.loads(lnx.sudo_command("nvme -id-ctrl {DEVICE} -o=json".format(DEVICE=device)))
        print "Output : " + str(op)
        return op["cntlid"]

    def getNvmSetId(self,lnx,ns):
        op = json.loads(lnx.sudo_command("nvme -id-ns {NS} -o=json".format(NS=ns)))
        print "Output : " + str(op)
        return op["nvmsetid"]


    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)[0]
            nvme_device_ns = nvme_device_name
            nvme_device = nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]



    def cleanup(self):
        self.storage_controller_template.cleanup()


class GenericCreateAttachDetachDelete(FunTestCase):

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
                                                                                  "uuid {}".format(i+1, vol_uuid[0]))
                self.vol_uuid_list.append(vol_uuid[0])

            # Do a nvme connect-all from the host
            for index, fs_obj in enumerate(self.fs_obj_list):
                attach_vol_result = self.blt_template.attach_volume(host_obj=self.hosts, fs_obj=fs_obj,
                                                                                   volume_uuid=self.vol_uuid_list[index],
                                                                                   validate_nvme_connect=True, discover=True,
                                                                                    raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")


            time.sleep(120)
            self.cleanupio()
            fun_test.test_assert(expression=True, message="Test completed {} Iteration".format(count + 1))


    def cleanupio(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
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
                    fun_test.test_assert(expression=delete_volume.status, message="Delete Volume {}".format(volume))

    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.blt_template


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
    #setup_bringup.add_test_case(ConnectAllMaxHosts())
    #setup_bringup.add_test_case(ConnectAllContinuous())
    #setup_bringup.add_test_case(ConnectAllContinuousMultiHost())


    setup_bringup.run()
