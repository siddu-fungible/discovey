from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import *
from scripts.storage.storage_helper import *
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


class C17808(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=1,
                              summary="c17808: Detach/Attach in loop with the host connected to the NVMe sub system",
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

        # Create a volume
        vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                 name=self.name, sfx=str(sfx))

        print "vol_uuid:", vol_uuid
        fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()

        # Attach the volume
        attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                           volume_uuid=vol_uuid,
                                                                           validate_nvme_connect=True,
                                                                           raw_api_call=True)
        fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Successful")
        self.attach_result = attach_vol_result
        print "attach_vol_result", attach_vol_result

        # disconnect from host
        port = attach_vol_result["data"]["uuid"]
        print "port:", port
        subsystem_nqn = attach_vol_result['data']['subsys_nqn']
        nsid = attach_vol_result['data']['nsid']
        host_handle = hosts[0].get_instance()

        nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=hosts[0],
                                                                                 subsys_nqn=subsystem_nqn,
                                                                                 nsid=nsid)
        host_handle.nvme_disconnect(device=nvme_device_name)
        fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                format(nvme_device_name, hosts[0].name))

        print "loop_count:", self.loop_count
        connect = False
        for counter in range(self.loop_count):
            if (counter == (self.loop_count - 1)):
                    connect = True
            # Lets wait for some time before we detach
            fun_test.sleep("Lets wait for some time before we detach..", seconds=5)
            port = attach_vol_result["data"]["uuid"]
            detach_vol_result = detach(fs_obj, port)
            print "detach_vol_result:", detach_vol_result
            fun_test.test_assert(expression=True, message="Detach Volume Successful")

            # Attach again!
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid,
                                                                               validate_nvme_connect=connect,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Successful")
            self.attach_result = attach_vol_result
            print "attach_vol_result", attach_vol_result
            print "attach_vol_result[data][uuid]", attach_vol_result["data"]["uuid"]

        # disconnect detach and delete finally
        nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=hosts[0],
                                                                                 subsys_nqn=subsystem_nqn,
                                                                                 nsid=nsid)
        host_handle.nvme_disconnect(device=nvme_device_name)
        fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                format(nvme_device_name, hosts[0].name))

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


class C17854(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=2,
                              summary="c17854:  Volume Create, Attach, Detach and Delete in a loop",
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


class C36894(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=3,
                              summary="C36894: Create 1K vols/DPU and delete the same - (no attach required) in a loop",
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

        sfx = 0
        min_volume_capacity = 1073741824
        fs_obj = self.fs_obj_list[0]
        storage_controller = fs_obj.get_storage_controller()
        raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
        response = raw_sc_api.get_pools()
        pool_uuid = str(response['data'].keys()[0])
        loc_capacity = str(response['data'][pool_uuid]['capacity'])
        max_volume_capacity = find_min_drive_capacity(storage_controller, 30) - (3 * 4096)
        max_no_of_volumes = (int)(loc_capacity) / min_volume_capacity
        self.capacity = max_volume_capacity
        self.loop_count = max_no_of_volumes
        print "capacity:", self.capacity, " # of vols:", self.loop_count

        body_volume_intent_create = BodyVolumeIntentCreate(name=self.name, vol_type=self.vol_type,
                                                           capacity=self.capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        body_volume_intent_create.vol_type = self.vol_type

        volumes = []
        print "updated loop_count:", self.loop_count
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

    def cleanup(self):
        self.total_volumes = fun_test.shared_variables["total_volumes"]
        print "total_volumes:", self.total_volumes
        pass


class C36892(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None

    def describe(self):
        pass
        self.set_test_details(id=4,
                              summary="C36892:Create N more volumes after 1000, delete existing N volumes and create N",
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

        sfx = 0
        min_volume_capacity = 1073741824
        fs_obj = self.fs_obj_list[0]
        storage_controller = fs_obj.get_storage_controller()
        raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
        response = raw_sc_api.get_pools()
        pool_uuid = str(response['data'].keys()[0])
        loc_capacity = str(response['data'][pool_uuid]['capacity'])
        max_volume_capacity = find_min_drive_capacity(storage_controller, 30) - (3 * 4096)
        max_no_of_volumes = (int)(loc_capacity) / min_volume_capacity
        self.capacity = max_volume_capacity
        self.loop_count = max_no_of_volumes
        print "capacity:", self.capacity, " # of vols:", self.loop_count

        body_volume_intent_create = BodyVolumeIntentCreate(name=self.name, vol_type=self.vol_type,
                                                           capacity=self.capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})

        body_volume_intent_create.vol_type = self.vol_type

        volumes = []
        print "updated loop_count:", self.loop_count
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

    def cleanup(self):
        self.total_volumes = fun_test.shared_variables["total_volumes"]
        print "total_volumes:", self.total_volumes
        pass


class C37533(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        pass
        self.set_test_details(id=5,
                              summary="c37533: attach >128 vols, detaching N existing volumes, attaching N more new",
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
        new_vols = []
        created_ports = []
        attach_result = []
        attach_vol_result = {}
        last_attach_result = {}
        print "loop_count:", self.loop_count
        for counter in range(128):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx=str(counter))

            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            created_vols.append(vol_uuid)
            if (counter == 127):
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
            last_attach_result = attach_vol_result

        print "created vols:", len(created_vols)
        print "created ports:", len(created_ports)
        fun_test.test_assert(expression=len(created_vols) == len(created_ports),
                             message="Attached all Volumes Successfully")

        # Create and attach 8 more vols
        connect = False
        for counter in range(8):
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                     name=self.name, sfx="new" + str(counter))

            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            new_vols.append(vol_uuid)

            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid,
                                                                               validate_nvme_connect=connect,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Failed")

        # disconnect from host first
        port = last_attach_result["data"]["uuid"]
        print "port:", port
        subsystem_nqn = last_attach_result['data']['subsys_nqn']
        nsid = last_attach_result['data']['nsid']
        host_handle = hosts[0].get_instance()

        nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=hosts[0],
                                                                                 subsys_nqn=subsystem_nqn,
                                                                                 nsid=nsid)
        to_disconnect = nvme_device_name[0:10]
        print "nvme_device_name to disconnect:", to_disconnect
        host_handle.nvme_disconnect(device=to_disconnect)
        fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                format(nvme_device_name, hosts[0].name))

        # detach 8 vols from previous list
        for counter in range(8):
            port = created_ports[len(created_ports) - counter]
            detach_vol_result = detach(fs_obj, port)
            print "detach_vol_result:", detach_vol_result
            fun_test.test_assert(expression=True, message="Detach Volume Successful port:".format(port))
            created_ports.remove(port)

        # attach newly created 8 vols
        for counter in range(8):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                               volume_uuid=new_vols[counter],
                                                                               validate_nvme_connect=connect,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Successful")
            attach_result.append(attach_vol_result)
            print "attach_vol_result", attach_vol_result
            print "self.attach_result[counter][data][uuid]", attach_result[counter]["data"]["uuid"]
            created_ports.append(attach_result[counter]["data"]["uuid"])

        # detach first 8 volumes now
        for counter in range(8):
            port = created_ports[counter]
            detach_vol_result = detach(fs_obj, port)
            print "detach_vol_result:", detach_vol_result
            fun_test.test_assert(expression=True, message="Detach Volume Successful port:".format(port))
            created_ports.remove(port)

        # Create and attach 8 more vols
        connect = False
        for counter in range(8):
            if (counter == 7):
                connect = True
            vol_uuid = create_volume(fs_obj=fs_obj, body_volume_intent_create=body_volume_intent_create,
                                        name=self.name, sfx="latest" + str(counter))

            print "vol_uuid:", vol_uuid
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            new_vols.append(vol_uuid)

            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                                volume_uuid=vol_uuid,
                                                                                validate_nvme_connect=connect,
                                                                                raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result["status"], message="Attach Volume Failed")

        fun_test.shared_variables["created_vols"] = created_vols
        fun_test.shared_variables["created_ports"] = created_ports
        fun_test.shared_variables["attach_result"] = attach_result
        fun_test.shared_variables["new_vols"] = new_vols

    def run(self):

        hosts = self.topology.get_available_host_instances()
        created_vols = fun_test.shared_variables["created_vols"]
        created_ports = fun_test.shared_variables["created_ports"]
        attach_result = fun_test.shared_variables["attach_result"]
        fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        fs_obj = self.fs_obj_list[0]
        attach_result_len = len(attach_result)
        host_obj = hosts[0]
        fun_test.shared_variables["host_obj"] = host_obj
        all_nvme_device_names = []
        print "len:", len, " all attached vols:", attach_result_len
        threads = list()
        for ctr in range(attach_result_len):
            print "subsys_nqn:", attach_result[ctr]['data']['subsys_nqn']

            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj,
                                                                                     subsys_nqn=attach_result[ctr][
                                                                                         'data']['subsys_nqn'],
                                                                                     nsid=attach_result[ctr][
                                                                                         'data']['nsid'])
            all_nvme_device_names.append(nvme_device_name)
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
        fio_thread(host_obj=host_obj, nvme_devices=all_nvme_device_names,
                   storage_controller_template=self.storage_controller_template)

        fun_test.shared_variables["all_nvme_device_names"] = all_nvme_device_names
        '''
        for index, thread in enumerate(threads):
            print "before joining thread"
            thread.join()
            print "thread done"
        '''

    def cleanup(self):
        created_vols = fun_test.shared_variables["created_vols"]
        new_vols = fun_test.shared_variables["new_vols"]
        created_ports = fun_test.shared_variables["created_ports"]
        fs_obj_list = fun_test.shared_variables["fs_obj_list"]
        fs_obj = self.fs_obj_list[0]
        host_obj = fun_test.shared_variables["host_obj"]
        all_nvme_device_names = fun_test.shared_variables["all_nvme_device_names"]
        host_handle = host_obj.get_instance()

        # disconnect first
        for counter in range(len(all_nvme_device_names)):
            device = all_nvme_device_names[counter]
            host_handle.nvme_disconnect(device=device)
            fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                    format(device, host_obj.name))
        # detach and delete
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





class C36988(C17854):
    def describe(self):
        self.set_test_details(id=6,
                              summary=" Volume Create, Attach, Detach and Delete in a loop (Encrypted)",
                              steps='''
                              ''')

    def setup(self):
        super(C36988, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(C36988, self).run()

    def cleanup(self):
        super(C36988, self).cleanup()





class C36969(C17808):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Detach/Attach in loop with host connected to NVMe sub system with Encryption",
                              steps='''
                              ''')

    def setup(self):
        super(C36969, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(C36969, self).run()

    def cleanup(self):
        super(C36969, self).cleanup()


class C37533_1():
    def describe(self):
        self.set_test_details(id=8,
                              summary="C37533:attach >128 vols, detaching N existing volumes, attaching N more new",
                              steps='''
                              ''')

    def setup(self):
        super(C37533_1, self).setup()

    def run(self):
        pass
        #pass  # Do not run FIO.
        super(C37533_1, self).run()

    def cleanup(self):
        super(C37533_1, self).cleanup()


class C37533_2(C37533):
    def describe(self):
        self.set_test_details(id=9,
                              summary="C37533:attach >128 enc vols, detaching N existing volumes, attaching N more new",
                              steps='''
                              ''')

    def setup(self):
        super(C37533_2, self).setup()

    def run(self):
        #pass  # Do not run FIO.
        super(C37533_2, self).run()

    def cleanup(self):
        super(C37533_2, self).cleanup()

if __name__ == "__main__":
    setup_bringup = BootupSetup()

    # C37533:attach >128 enc vols, detaching N existing volumes, attaching N more new"
    setup_bringup.add_test_case(C37533_1())
    setup_bringup.add_test_case(C37533_2())

    # Detach/Attach in loop with host connected to NVMe sub system"
    setup_bringup.add_test_case(C17808())
    setup_bringup.add_test_case(C36969())

    #  Volume Create, Attach, Detach and Delete in a loop
    setup_bringup.add_test_case(C17854())
    setup_bringup.add_test_case(C36988())



    # Create 1K vols/DPU and delete the same - (no attach required) in a loop"
    setup_bringup.add_test_case(C36894())

    # Create N more volumes after creating 1000 volumes, delete existing N volumes and create N
    setup_bringup.add_test_case(C36892())
    setup_bringup.run()
