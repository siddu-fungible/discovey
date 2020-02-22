from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.system import utils


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
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

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        self.topology = fun_test.shared_variables["topology"]
        parsing = True

        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("json file being used: {}".format(testcase_file))
        testcase_dict = utils.parse_file_to_json(testcase_file)

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(parsing, "Parsing json file for this {} testcase".format(testcase))

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "volume_count" in job_inputs:
            self.volume_count = job_inputs["volume_count"]
        if "encrypt" in job_inputs:
            self.encrypt = job_inputs["encrypt"]
        if "dpu_count" in job_inputs:
            self.dpu_count = job_inputs["dpu_count"]
        if "attach" in job_inputs:
            self.attach = job_inputs["attach"]
        if "detach" in job_inputs:
            self.detach = job_inputs["detach"]
        if "delete" in job_inputs:
            self.delete = job_inputs["delete"]
        if "format_drive" in job_inputs:
            self.format_drive = job_inputs["format_drive"]
        else:
            self.format_drive = False
        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False

        name = "blt_vol"
        vol_type = VolumeTypes().LOCAL_THIN
        compression_effort = False
        encrypt = False

        fs_obj_list = []

        host_obj_list = []

        vol_uuid_list = []  # Its a list of lists.

        # make a list of FS1600s
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = fs_obj_list

        # Make a list of hosts
        topo_host_count = 0
        hosts = self.topology.get_available_host_instances()
        if not isinstance(hosts, list):
            host_obj_list.append(hosts)
            topo_host_count = len(hosts)
        else:
            host_obj_list = hosts
            topo_host_count = 1

        if self.dpu_count == 2:
            dpu_indexes = [0, 1]
        else:
            dpu_indexes = [0]

        connect_needed = False

        if self.encrypt == "Y":
            encrypt = True

        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=self.already_deployed, dpu_indexes=dpu_indexes,
                                                    format_drives=self.format_drive)

        # Make a list of vol uuids by creating volume_count volumes for each fs_obj in fs_obj_list
        for i in range(self.volume_count):
            suffix = utils.generate_uuid(length=4)
            body_volume_intent_create = BodyVolumeIntentCreate(name=name + suffix + "_" + str(i),
                                                               vol_type=vol_type, capacity=self.capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={})
            vol_uuid = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                      body_volume_intent_create=body_volume_intent_create)

            vol_uuid_list.append(vol_uuid)
            fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful {}".format(i))
            detachable = False
            if self.attach == "Y":
                if i == (self.volume_count - 1):
                    connect_needed = True
                for j in range(len(vol_uuid_list[i])):
                    attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj_list[0],
                                                                                       fs_obj=fs_obj_list[0],
                                                                                       volume_uuid=vol_uuid_list[i][j],
                                                                                       validate_nvme_connect=connect_needed,
                                                                                       raw_api_call=True)
                    print "attach_vol_result[data]:", attach_vol_result["data"]
                    if attach_vol_result["data"]:
                        print "attach volume result:", attach_vol_result, \
                            " \nattach_volume_result[data][uuid]:", attach_vol_result["data"]["uuid"]
                        detachable = True

                    fun_test.test_assert(expression=attach_vol_result["data"],
                                         message="Attach Volume {} Successful".format(vol_uuid_list[i][j]))
                    if self.detach == "Y" and detachable:
                        storage_controller = fs_obj_list[0].get_storage_controller()
                        port = attach_vol_result[0]["data"]["uuid"]
                        detach_vol_result = storage_controller.storage_api.delete_port(port_uuid=port)

                        print "detach_vol_result:", detach_vol_result
                        fun_test.test_assert(expression=detach_vol_result,
                                             message="Detach Volume {} Successful".format(vol_uuid_list[i][j]))
            if self.delete == "Y":
                storage_controller = fs_obj_list[0].get_storage_controller()
                delete_vol_result = storage_controller.storage_api.delete_volume(volume_uuid=vol_uuid_list[i][j])
                print "delete_vol_result", delete_vol_result
                fun_test.test_assert(expression=delete_vol_result,
                                     message="Delete Volume {} Successful".format(vol_uuid_list[i][j]))
                vol_uuid_list[i][j] = ""

        print "vol_uuid_list:", vol_uuid_list

    def run(self):
        hosts = self.topology.get_available_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
                                                                                filename="/dev/"
                                                                                + str(nvme_device_name[0]))
            fun_test.test_assert(expression=traffic_result, message="Host : {} FIO traffic result".format(host_obj.name))
            fun_test.log(traffic_result)

    def cleanup(self):
        pass
        self.storage_controller_template.cleanup()


class BLTScaleNVolumes1Host1FSScale(RunStorageApiCommands):
    def describe(self):
        self.set_test_details(id=1,
                              summary="create-attach in loop",
                              steps='''
                              ''')

    def setup(self):
        super(BLTScaleNVolumes1Host1FSScale, self).setup()

    def run(self):
        pass  # Do not run FIO.
        #super(BLTScaleNVolumes1Host1FSScale, self).run()

    def cleanup(self):
        super(BLTScaleNVolumes1Host1FSScale, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BLTScaleNVolumes1Host1FSScale())
    setup_bringup.run()
