from lib.system.fun_test import *

fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.system import utils
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *
import copy

class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
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

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=self.already_deployed)
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template

        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)
        fs_obj = fs_obj_list[0]
        self.sc_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
        self.hosts = self.topology.get_available_host_instances()

        self.min_drive_capacity = find_min_drive_capacity(self.sc_dpcsh_obj)
        self.drive_margin = 12288
        fun_test.shared_variables["min_drive_capacity"] = self.min_drive_capacity
        fun_test.shared_variables["drive_margin"] = self.drive_margin

    def cleanup(self):
        self.topology.cleanup()


class BLTVolumes(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create Volume and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self, name, capacity=160027797094, compression_effort=False, encrypt=False):

        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        vol_type = VolumeTypes().LOCAL_THIN
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})


        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

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

    def run(self):
        print("run section")

    def cleanup(self):
        pass


class NameParameter(BLTVolumes):
    def describe(self):

        self.set_test_details(id=3,
                              summary="Create volume with invalid values for API parameter name",
                              test_rail_case_ids=["C19178"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        str = "abc"
        name_entries = [1234, str*256, "goold_blt_name", "$"+str, "blt_vol_1", str+"$"]
        for kk in range(len(name_entries)):
            fun_test.log("Trying to create Volume with name parameter set to {}".format(name_entries[kk]))
            super(NameParameter, self).setup(name=name_entries[kk])

    def run(self):
        super(NameParameter, self).run()

    def cleanup(self):
        super(NameParameter, self).cleanup()


class CapacityParameter(BLTVolumes):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Create volume with invalid values for API parameter capacity",
                              test_rail_case_ids=["C19178"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        min_capacity = fun_test.shared_variable["min_drive_capacity"]
        drive_margin = fun_test.shared_variable["drive_margin"]
        capacity_entries = [-123445455, 0, min_capacity, min_capacity-drive_margin]
        for kk in range(len(capacity_entries)):
            fun_test.log("Trying to create Volume with capacity parameter set to {}".format(capacity_entries[kk]))
            super(CapacityParameter, self).setup(name="blt_vol_capacity", capacity=capacity_entries[kk])

    def run(self):
        super(CapacityParameter, self).run()

    def cleanup(self):
        super(CapacityParameter, self).cleanup()

class EncryptParameter(BLTVolumes):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Create volume with invalid values for API parameter encrypt",
                              test_rail_case_ids=["C19178"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        min_capacity = fun_test.shared_variable["min_drive_capacity"]
        drive_margin = fun_test.shared_variable["drive_margin"]
        capacity_entry = min_capacity - drive_margin
        encrypt_entries = [invalid, 0, "false", False, True, "true"]
        for kk in range(len(encrypt_entries)):
            fun_test.log("Trying to create Volume with encrypt parameter set to {}".format(encrypt_entries[kk]))
            super(EncryptParameter, self).setup(name="blt_vol_encrypt", capacity=capacity_entry, encrypt=encrypt_entries[kk])

    def run(self):
        super(EncryptParameter, self).run()

    def cleanup(self):
        super(EncryptParameter, self).cleanup()


class MissingParameter(BLTVolumes):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create volume with missing API parameters",
                              test_rail_case_ids=["C19182"],
                              steps='''1. Make sure API server is up and running
                              2. Create volumes using API Call which has missing  mandatory parameters
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        min_capacity = fun_test.shared_variable["min_drive_capacity"]
        drive_margin = fun_test.shared_variable["drive_margin"]
        capacity_entry = min_capacity - drive_margin
        missing_entries = ["name", "capacity", "vol_type", "data_protection", "all", "none"]

        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        vol_type = VolumeTypes().LOCAL_THIN
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})


        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

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


        for kk in range(len(missing_entries)):
            fun_test.log("Trying to create Volume with missing parameter set to {}".format(missing_entries[kk]))
            
    def run(self):
        super(EncryptParameter, self).run()

    def cleanup(self):
        super(EncryptParameter, self).cleanup()

class MissingParameter(BLTVolumes):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Create volume with missing API parameters",
                              test_rail_case_ids=["C19182"],
                              steps='''1. Make sure API server is up and running
                              2. Create volumes using API Call which has missing  mandatory parameters
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        min_capacity = fun_test.shared_variable["min_drive_capacity"]
        drive_margin = fun_test.shared_variable["drive_margin"]
        capacity_entry = min_capacity - drive_margin
        compression_effort = False
        encrypt = False
        missing_entries = ["name", "capacity", "vol_type", "data_protection", "all", "none"]

        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        vol_type = VolumeTypes().LOCAL_THIN

        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")


        for kk in range(len(missing_entries)):
            fun_test.log("Trying to create Volume with missing parameter set to {}".format(missing_entries[kk]))

            if (missing_entries[kk]=="name"):
                body_volume_intent_create = BodyVolumeIntentCreate(vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})
            if (missing_entries[kk]=="capacity"):
                body_volume_intent_create = BodyVolumeIntentCreate(name="missing_capacity",vol_type=vol_type,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})

            if (missing_entries[kk]=="vol_type"):
                body_volume_intent_create = BodyVolumeIntentCreate(name="missing_capacity",capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})
            if (missing_entries[kk]=="data_protection"):
                body_volume_intent_create = BodyVolumeIntentCreate(name="missiong_data_protection",vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt)
            if (missing_entries[kk]=="all"):
                body_volume_intent_create = BodyVolumeIntentCreate(compression_effort=compression_effort,
                                                               encrypt=encrypt)

            if (missing_entries[kk]=="none"):
                body_volume_intent_create = BodyVolumeIntentCreate(name="all_good_params_blt", vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})


            fs_obj_list = []
            for dut_index in self.topology.get_available_duts().keys():
                fs_obj = self.topology.get_dut_instance(index=dut_index)
                fs_obj_list.append(fs_obj)

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

    def run(self):
        super(MissingParameter, self).run()

    def cleanup(self):
        super(MissingParameter, self).cleanup()




if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(NameParameter())
    setup_bringup.add_test_case(CapacityParameter())
    setup_bringup.add_test_case(EncryptParameter())
    setup_bringup.add_test_case(MissingParameter())
    setup_bringup.run()
