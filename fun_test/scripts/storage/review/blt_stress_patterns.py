from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes

'''
  // Stress patterns: SINGLE HOST SCENARIOS
  // "C": Create, Create ...
  // "CA" : Create, Attach, Create, Attach...(Different volumes)
  // "CAA" : Create, Attach, Attach, Attach.... (Same volume, same host, -ve test)
  // "CADt" : Create, Attach, Detach, Create, Attach, Detach... (Different Volumes)
  // "CADtADt" : Create, Attach, Detach, Attach, Detach... (Same volume)
  // "CADtDl" : Create, Attach, Detach, Delete, Create, Attach, Detach, Delete...(Different vols)
  // "CADtDlADtDl": Create Attach Detach Delete, Attch, Detach, Delete (Same volume)
'''


class BootupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bootup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))

        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False

        if "format_drive" in job_inputs:
            self.format_drive = job_inputs["format_drive"]
        else:
            self.format_drive = False

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        self.topology.cleanup()


class RunStorageApiCommands(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create Volume and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "loop_count" in job_inputs:
            self.loop_count = job_inputs["loop_count"]
        else:
            self.loop_count = 5

        if "pattern" in job_inputs:
            self.pattern = job_inputs["pattern"]
        else:
            self.pattern = "CADtADt"

        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False

        if "format_drive" in job_inputs:
            self.format_drive = job_inputs["format_drive"]
        else:
            self.format_drive = False

        name = "blt_vol"
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=self.already_deployed,
                                                    format_drives=self.format_drive)

        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

        vol_uuid_list = self.storage_controller_template.\
            create_volume(fs_obj=fs_obj_list, body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for counter in range(self.loop_count):
            for index, fs_obj in enumerate(fs_obj_list):
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                                   volume_uuid=vol_uuid_list[index],
                                                                                   validate_nvme_connect=True,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")
                self.attach_result = attach_vol_result
                port = attach_vol_result[0]["data"]["uuid"]
                self.detach(fs_obj_list[0], port)

        self.delete(fs_obj_list[0], vol_uuid_list[0])

    def run(self):
        pass
        hosts = self.topology.get_available_host_instances()
        for host_obj in hosts:
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj,
                                                                                     subsys_nqn=self.attach_result[
                                                                                         'data']['subsys_nqn'],
                                                                                     nsid=self.attach_result[
                                                                                         'data']['nsid'])
            storage_traffic_obj = StorageTrafficTemplate(storage_operations_template=self.storage_controller_template)
            traffic_result = storage_traffic_obj.fio_basic(host_obj=host_obj.get_instance(), filename=nvme_device_name)
            fun_test.test_assert(expression=traffic_result,
                                 message="Host : {} FIO traffic result".format(host_obj.name))
            fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup(fun_test.is_current_test_case_failed())

    def detach(self, fs_obj, port):
        storage_controller = fs_obj.get_storage_controller()
        detach_vol_result = storage_controller.storage_api.delete_port(port_uuid=port)

    def delete(self, fs_obj, uuid):
        storage_controller = fs_obj.get_storage_controller()
        delete_vol_result = storage_controller.storage_api.delete_volume(volume_uuid=uuid)


if __name__ == "__main__":
    setup_bringup = BootupSetup()
    setup_bringup.add_test_case(RunStorageApiCommands())
    setup_bringup.run()
