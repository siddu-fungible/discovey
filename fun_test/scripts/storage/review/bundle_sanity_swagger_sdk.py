from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate, EcVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes


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

    def cleanup(self):
        self.topology.cleanup()


class GenericStorageTest(FunTestCase):
    test_case_id = 1
    topology = None
    storage_controller_template = None
    attach_result = None
    storage_traffic_template = None
    VOL_TYPE = VolumeTypes().LOCAL_THIN
    IO_DEPTH = 2
    CAPACITY = 1073741824
    already_deployed = False

    def describe(self):
        self.set_test_details(id=self.test_case_id,
                              summary="Create Volume using API and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol"

        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=self.VOL_TYPE, capacity=self.CAPACITY,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        if self.VOL_TYPE == VolumeTypes().LOCAL_THIN:
            self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        elif self.VOL_TYPE == VolumeTypes().EC:
            self.storage_controller_template = EcVolumeOperationsTemplate(topology=self.topology)

        self.storage_controller_template.initialize(already_deployed=self.already_deployed)

        fs_obj_list = [self.topology.get_dut_instance(index=dut_index)
                       for dut_index in self.topology.get_available_duts().keys()]

        vol_uuid_list = self.storage_controller_template.create_volume(
            fs_obj=fs_obj_list, body_volume_intent_create=body_volume_intent_create)
        fun_test.shared_variables["vol_uuid_list"] = vol_uuid_list
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts[0], fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")
            self.attach_result = attach_vol_result

    def run(self):
        hosts = self.topology.get_available_host_instances()
        self.storage_traffic_template = StorageTrafficTemplate(
            storage_operations_template=self.storage_controller_template)

        for host_obj in hosts:
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj,
                                                                                     subsys_nqn=self.attach_result[
                                                                                         'data']['subsys_nqn'],
                                                                                     nsid=self.attach_result[
                                                                                         'data']['nsid'])
            fun_test.test_assert(expression=nvme_device_name,
                                 message="NVMe device found on Host : {}".format(nvme_device_name))

            fio_integrity = self.storage_traffic_template.fio_with_integrity_check(
                host_linux_handle=host_obj.get_instance(), filename=nvme_device_name, numjobs=1, iodepth=self.IO_DEPTH)
            fun_test.test_assert(message="Do FIO integrity check", expression=fio_integrity)
            fun_test.shared_variables["nvme_device_name"] = nvme_device_name
            fun_test.shared_variables["attach_result"] = self.attach_result
            break

    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template
        fun_test.shared_variables["storage_traffic_template"] = self.storage_traffic_template


class ConfigPersistenceAfterReset(FunTestCase):
    topology = None
    storage_controller_template = None
    IO_DEPTH = 2

    def describe(self):
        self.set_test_details(id=2,
                              summary="Reset FS1600 and Do IO from host",
                              steps='''
                                 1. Reset FS1600 
                                 2. Make sure API server is up and running
                                 3. Make sure Volume is Present
                                 4. Make sure Host sees NVMe device
                                 5. Run FIO from host
                                 ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        threads_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=self.reset_and_health_check,
                                                      fs_obj=fs_obj)
            threads_list.append(thread_id)

        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
        fun_test.sleep(message="Wait before sending Dataplane IP commands", seconds=60)  # WORKAROUND
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            self.storage_controller_template.verify_dataplane_ip(storage_controller=storage_controller,
                                                                 fs_obj=fs_obj)
            vol_uuid_list = fun_test.shared_variables["vol_uuid_list"]
            timer = FunTimer(max_time=120)
            while not timer.is_expired():
                if self.storage_controller_template.get_volume_attach_status(fs_obj=fs_obj,
                                                                             volume_uuid=vol_uuid_list[0]):
                    fun_test.test_assert(expression=True,
                                         message="Volume {} attached to a port".format(vol_uuid_list[0]))
                    break
                fun_test.sleep(message="Waiting for Volume UUID to be attached to a port", seconds=15)

    def run(self):
        storage_traffic_template = fun_test.shared_variables["storage_traffic_template"]
        attach_result = fun_test.shared_variables["attach_result"]

        for host_obj in self.topology.get_available_host_instances():
            nvme_device_name_before_reboot = fun_test.shared_variables["nvme_device_name"]

            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj,
                                                                                     subsys_nqn=attach_result['data'][
                                                                                         'subsys_nqn'],
                                                                                     nsid=attach_result['data'][
                                                                                         'nsid'])
            fun_test.test_assert_expected(expected=nvme_device_name_before_reboot, actual=nvme_device_name,
                                          message="NVMe device found on Host after FS reboot: {}".format(
                                              nvme_device_name))
            fio_integrity = storage_traffic_template.fio_with_integrity_check(host_linux_handle=host_obj.get_instance(),
                                                                              filename=nvme_device_name,
                                                                              numjobs=1, iodepth=self.IO_DEPTH,
                                                                              verify_integrity=True)
            fun_test.test_assert(message="Do FIO integrity check", expression=fio_integrity)
            break

    def cleanup(self):
        self.storage_controller_template.cleanup(test_result_failed=fun_test.is_current_test_case_failed())
        if not fun_test.is_current_test_case_failed():
            hosts = self.topology.get_available_host_instances()
            for host_obj in hosts:
                self.storage_controller_template.host_diagnostics(host_obj=host_obj.get_instance())

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset()
        fs_obj.come.ensure_expected_containers_running()
        # fs_obj.re_initialize()
        fun_test.test_assert(expression=self.storage_controller_template.get_health(fs_obj),
                             message="{}: API server health".format(fs_obj))


class BltApiStorageTest(GenericStorageTest):
    VOL_TYPE = VolumeTypes().LOCAL_THIN

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create BLT Volume using API and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

class EcApiStorageTest(GenericStorageTest):
    VOL_TYPE = VolumeTypes().EC
    test_case_id = 3
    already_deployed = True

    def describe(self):
        self.set_test_details(id=self.test_case_id,
                              summary="Create EC Volume using API and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BltApiStorageTest())
    setup_bringup.add_test_case(ConfigPersistenceAfterReset())
    setup_bringup.add_test_case(EcApiStorageTest())
    setup_bringup.run()
