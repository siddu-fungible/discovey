from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import *
from lib.system import utils


def create_volume(fs_obj, body_volume_intent_create, name, sfx):
    """
    Create a volume for the fs_obj
    :param fs_obj: Single fs object
    :param body_volume_intent_create: object of class BodyVolumeIntentCreate with volume details
    :return: single vol_uuid
    """
    body_volume_intent_create.name = name + str(sfx)
    result = ""
    storage_controller = fs_obj.get_storage_controller()
    try:
        create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
        vol_uuid = create_vol_result.data.uuid
        result = vol_uuid
    except Exception as e:
        fun_test.critical("Exception when creating volume on fs %s: %s\n" % (fs_obj, e))
    return result


def detach(fs_obj, port):
    storage_controller = fs_obj.get_storage_controller()
    detach_vol_result = storage_controller.storage_api.delete_port(port_uuid=port)
    return detach_vol_result


def delete(fs_obj, uuid):
    storage_controller = fs_obj.get_storage_controller()
    delete_vol_result = storage_controller.storage_api.delete_volume(volume_uuid=uuid)
    return delete_vol_result


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
            self.format_drive = True

        if "dpu_count" in job_inputs:
            self.dpu_count = job_inputs["dpu_count"]
        else:
            self.dpu_count = 1

        if self.dpu_count == 2:
            dpu_indexes = [0, 1]
        else:
            dpu_indexes = [0]

        fun_test.shared_variables["already_deployed"] = self.already_deployed
        fun_test.shared_variables["format_drive"] = self.format_drive

        topology_helper = TopologyHelper()
        print "self.already_deployed:", self.already_deployed
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology,
                                                                       api_logging_level=logging.ERROR)
        self.storage_controller_template.initialize(already_deployed=self.already_deployed,
                                                    format_drives=self.format_drive,
                                                    dpu_indexes=dpu_indexes)
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list

    def cleanup(self):
        self.storage_controller_template.cleanup()
        self.topology.cleanup()


class CADtADt(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=1,
                              summary="CADtADt",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        testcase = self.__class__.__name__
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("json file being used: {}".format(testcase_file))
        testcase_dict = utils.parse_file_to_json(testcase_file)
        parsing = True

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(parsing, "Parsing json file for this {} testcase".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        self.name = "blt_VOL"
        self.vol_type = VolumeTypes().LOCAL_THIN
        compression_effort = False
        self.topology = fun_test.shared_variables["topology"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "loop_count" in job_inputs:
            self.loop_count = job_inputs["loop_count"]

        if "pattern" in job_inputs:
            self.pattern = job_inputs["pattern"]

        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]

        if "encrypt" in job_inputs:
            self.encrypt = job_inputs["encrypt"]

        if "volume_count" in job_inputs:
            self.volume_count = job_inputs["volume_count"]

        if self.encrypt == "Y":
            encrypt = True
        else:
            encrypt = False

        print "capacity:", self.capacity, " loop:", self.loop_count, " pattern:", self.pattern

        body_volume_intent_create = BodyVolumeIntentCreate(name=self.name, vol_type=self.vol_type,
                                                           capacity=self.capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        body_volume_intent_create.vol_type = self.vol_type

        sfx = 0

        fs_obj = self.fs_obj_list[0]
        vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                 name=self.name, sfx=str(sfx))

        print "vol_uuid:", vol_uuid
        fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        print "loop_count:", self.loop_count
        for counter in range(self.loop_count):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                                volume_uuid=vol_uuid,
                                                                                validate_nvme_connect=False,
                                                                                raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Successful")
            self.attach_result = attach_vol_result
            print "attach_vol_result", attach_vol_result
            print "attach_vol_result[data][uuid]", attach_vol_result["data"]["uuid"]
            # Lets wait for some time before we detach
            fun_test.sleep("Lets wait for some time before we detach..", seconds=5)
            port = attach_vol_result["data"]["uuid"]
            detach_vol_result = detach(fs_obj, port)
            print "detach_vol_result:", detach_vol_result
            fun_test.test_assert(expression=True, message="Detach Volume Successful")

        delete_vol_result = delete(fs_obj, vol_uuid)
        print "delete_vol_result:", delete_vol_result
        fun_test.test_assert(expression=delete_vol_result, message="Delete Volume Successful")

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
        pass
        self.storage_controller_template.cleanup(fun_test.is_current_test_case_failed())


class CADtADt1(CADtADt):
    def describe(self):
        self.set_test_details(id=1,
                              summary="create. attach-detach in loop, delete",
                              steps='''
                              ''')

    def setup(self):
        super(CADtADt1, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CADtADt1, self).run()

    def cleanup(self):
        super(CADtADt1, self).cleanup()


class CADtADt2(CADtADt):
    def describe(self):
        self.set_test_details(id=2,
                              summary="create. attach-detach in loop, delete with Encryption",
                              steps='''
                              ''')

    def setup(self):
        super(CADtADt2, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CADtADt2, self).run()

    def cleanup(self):
        super(CADtADt2, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BootupSetup()
    setup_bringup.add_test_case(CADtADt1())
    setup_bringup.add_test_case(CADtADt2())
    setup_bringup.run()