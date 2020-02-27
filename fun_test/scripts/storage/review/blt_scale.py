from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import *
from lib.system import utils

'''
  // Stress patterns: SINGLE HOST SCENARIOS
  // "C": Create, Create ...
  // "CD": Create, Delete, Create, Delete (Single volume)
  // "CCDD": Create, Create, Create, ... Delete, Delete, Delete...(N volumes)
  // "CA" : Create, Attach, Create, Attach...(Different volumes)
  // "CAA" : Create, Attach, Attach, Attach.... (Same volume, same host, -ve test)
  // "CADt" : Create, Attach, Detach, Create, Attach, Detach... (Different Volumes)
  // "CADtADt" : Create, Attach, Detach, Attach, Detach... (Same volume)
  // "CADtDl" : Create, Attach, Detach, Delete, Create, Attach, Detach, Delete...(Different vols)
  // "CADtDlADtDl": Create Attach Detach Delete, Attch, Detach, Delete (Same volume)
'''


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


def fio_thread(host_obj, nvme_device, storage_controller_template):
    print "fio_thread: nvme_device:", nvme_device
    storage_traffic_obj = StorageTrafficTemplate(storage_operations_template=storage_controller_template)
    traffic_result = storage_traffic_obj.fio_basic(host_obj=host_obj.get_instance(), filename=nvme_device)
    fun_test.test_assert(expression=traffic_result,
                         message="Host : {} FIO traffic result".format(host_obj.name))
    fun_test.log(traffic_result)


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
            self.already_deployed = True

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


class CADtDl(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=2,
                              summary="CADtDl",
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

        print "loop_count:", self.loop_count
        for counter in range(self.loop_count):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx=str(sfx))

            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            hosts = self.topology.get_available_host_instances()

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


class CCDlDl(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=3,
                              summary="CCDlDl",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              '''
                              )

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
        volumes = []
        print "loop_count:", self.loop_count
        for outer_counter in range(3):
            self.total_volumes = 0
            for counter in range(self.loop_count):
                vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                        name=self.name, sfx=str(counter))
                print "vol_uuid:", vol_uuid
                fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
                volumes.append(vol_uuid)
                self.total_volumes += 1
                fun_test.shared_variables["total_volumes"] = self.total_volumes

            for counter in range(len(volumes)):
                delete_vol_result = delete(fs_obj, volumes[counter])
                print "delete_vol_result:", delete_vol_result
                fun_test.test_assert(expression=delete_vol_result, message="Delete Volume Successful")
                print "iteration:", outer_counter, "total_volumes:", self.total_volumes

    def run(self):
        pass  # Do not run FIO.
        #super(CCDlDl, self).run()

    def cleanup(self):
        self.total_volumes = fun_test.shared_variables["total_volumes"]
        print "total_volumes:", self.total_volumes
        pass
        super(CCDlDl, self).cleanup()


class CreateDeleteNCreateAgain(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=3,
                              summary="CreateDeleteNCreateAgain",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              '''
                              )

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
        volumes = []
        print "loop_count:", self.loop_count
        for counter in range(self.loop_count):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx=str(counter))
            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            volumes.append(vol_uuid)

        # now delete first 25 volumes
        for counter1 in range(25):
            vol_uuid = volumes[counter1]
            delete_vol_result = delete(fs_obj, volumes[counter1])
            print "delete_vol_result:", delete_vol_result
            fun_test.test_assert(expression=delete_vol_result, message="Delete Volume Successful")
            volumes.remove(vol_uuid)

        # now create 25 volumes again
        for counter2 in range(25):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx="new"+ str(counter2))
            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            volumes.insert(counter2, vol_uuid)

        # finally delete all of them
        for counter3 in range(len(volumes)):
            delete_vol_result = delete(fs_obj, volumes[counter3])
            print "delete_vol_result:", delete_vol_result
            fun_test.test_assert(expression=delete_vol_result, message="Delete Volume Successful")

    def run(self):
        pass  # Do not run FIO.
        # super(CCDlDl, self).run()

    def cleanup(self):
        pass
        super(CreateDeleteNCreateAgain, self).cleanup()


class ScaleMaxAttached(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        pass
        self.set_test_details(id=2,
                              summary="ScaleMaxAttached",
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

        fs_obj = self.fs_obj_list[0]
        hosts = self.topology.get_available_host_instances()
        connect = False
        created_vols = []
        created_ports = []
        attach_result = []
        print "loop_count:", self.loop_count
        for counter in range(self.loop_count):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx=str(counter))

            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            created_vols.append(vol_uuid)
            if (counter == self.loop_count -1):
                connect = True
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid,
                                                                               validate_nvme_connect=connect,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Successful")
            attach_result.append(attach_vol_result)
            print "attach_vol_result", attach_vol_result
            print "self.attach_result[counter][data][uuid]", attach_result[counter]["data"]["uuid"]
            created_ports.append(attach_result[counter]["data"]["uuid"])

        print "created vols:", len(created_vols)
        print "created ports:", len(created_ports)
        fun_test.test_assert(expression=len(created_vols) == len(created_ports),
                             message="Attached all Volumes Successfully")

        fun_test.shared_variables["created_vols"] = created_vols
        fun_test.shared_variables["created_ports"] = created_ports
        fun_test.shared_variables["attach_result"] = attach_result

    def run(self):

        hosts = self.topology.get_available_host_instances()
        created_vols = fun_test.shared_variables["created_vols"]
        created_ports = fun_test.shared_variables["created_ports"]
        attach_result = fun_test.shared_variables["attach_result"]
        fs_obj_list = fun_test.shared_variables["fs_obj_list"]
        fs_obj = self.fs_obj_list[0]
        attach_result_len = len(attach_result)
        host_obj = hosts[0]
        print "len:", len, " all attached vols:", attach_result_len
        threads = list()
        for ctr in range(attach_result_len):
            print "subsys_nqn:", attach_result[ctr]['data']['subsys_nqn']

            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj,
                                                                                     subsys_nqn=attach_result[ctr][
                                                                                         'data']['subsys_nqn'],
                                                                                     nsid=attach_result[ctr][
                                                                                         'data']['nsid'])
            '''
            storage_traffic_obj = StorageTrafficTemplate(storage_operations_template=self.storage_controller_template)
            traffic_result = storage_traffic_obj.fio_basic(host_obj=host_obj.get_instance(), filename=nvme_device_name)
            fun_test.test_assert(expression=traffic_result,
                                 message="Host : {} FIO traffic result".format(host_obj.name))
            fun_test.log(traffic_result)
            '''

            thread_args = {}
            thread_args.update({'host_obj': host_obj})
            thread_args.update({'nvme_device': nvme_device_name})
            thread_args.update({'storage_controller_template': self.storage_controller_template})
            print "thread args:", thread_args
            x = threading.Thread(target=fio_thread, args=(host_obj, nvme_device_name, self.storage_controller_template))
            threads.append(x)
            x.start()

            '''
            fio_thread(host_obj=host_obj, nvme_device=nvme_device_name,
                       storage_controller_template=self.storage_controller_template)
            '''
            for index, thread in enumerate(threads):
                print "before joining thread"
                thread.join()
                print "thread done"

    def cleanup(self):
        created_vols = fun_test.shared_variables["created_vols"]
        created_ports = fun_test.shared_variables["created_ports"]
        fs_obj_list = fun_test.shared_variables["fs_obj_list"]
        fs_obj = self.fs_obj_list[0]
        for counter in range(len(created_vols)):
            # Lets wait for some time before we detach
            fun_test.sleep("Lets wait for some time before we detach..", seconds=5)
            port = created_ports[counter]
            detach_vol_result = detach(fs_obj, port)
            print "detach_vol_result[status]:", detach_vol_result["status"]
            fun_test.test_assert(expression=True, message="Detach Volume Successful")
            vol_uuid = created_vols[counter]
            delete_vol_result = delete(fs_obj, vol_uuid)
            print "delete_vol_result:", delete_vol_result
            fun_test.test_assert(expression=delete_vol_result, message="Delete Volume Successful")
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


class CCDlDl1(CCDlDl):
    def describe(self):
        self.set_test_details(id=3,
                              summary="create in loop, detach in loop",
                              steps='''
                              ''')

    def setup(self):
        super(CCDlDl1, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CCDlDl1, self).run()

    def cleanup(self):
        super(CCDlDl1, self).cleanup()


class CreateDeleteNCreateAgain1(CreateDeleteNCreateAgain):
    def describe(self):
        self.set_test_details(id=4,
                              summary="CreateDeleteNCreateAgain1",
                              steps='''
                              ''')

    def setup(self):
        super(CreateDeleteNCreateAgain1, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CreateDeleteNCreateAgain1, self).run()

    def cleanup(self):
        super(CreateDeleteNCreateAgain1, self).cleanup()

class CADtDl1(CADtDl):
    def describe(self):
        self.set_test_details(id=5,
                              summary="create attach detach delete in loop",
                              steps='''
                              ''')

    def setup(self):
        super(CADtDl1, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CADtDl1, self).run()

    def cleanup(self):
        super(CADtDl1, self).cleanup()

class CADtDl2(CADtDl):
    def describe(self):
        self.set_test_details(id=6,
                              summary="create attach detach delete in loop with encryption",
                              steps='''
                              ''')

    def setup(self):
        super(CADtDl2, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(CADtDl2, self).run()

    def cleanup(self):
        super(CADtDl2, self).cleanup()


class ScaleMaxAttached1(ScaleMaxAttached):
    def describe(self):
        self.set_test_details(id=7,
                              summary="ScaleMaxAttached1",
                              steps='''
                              ''')

    def setup(self):
        super(ScaleMaxAttached1, self).setup()

    def run(self):
        #pass  # Do not run FIO.
        super(ScaleMaxAttached1, self).run()

    def cleanup(self):
        super(ScaleMaxAttached1, self).cleanup()

if __name__ == "__main__":
    setup_bringup = BootupSetup()
    #setup_bringup.add_test_case(CCDlDl1())
    #setup_bringup.add_test_case(CreateDeleteNCreateAgain1())
    #setup_bringup.add_test_case(CADtDl2())
    #setup_bringup.add_test_case(CADtADt1())
    #setup_bringup.add_test_case(CADtADt2())
    #setup_bringup.add_test_case(CADtDl1())
    setup_bringup.add_test_case(ScaleMaxAttached1())
    setup_bringup.run()
