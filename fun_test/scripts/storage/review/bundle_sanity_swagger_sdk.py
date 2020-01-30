from lib.system.fun_test import *
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.review.storage_operations_template import BltVolumeOperationsTemplate
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


class BltApiStorageTest(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
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
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize()

        fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

        vol_uuid_dict = self.storage_controller_template.create_volume(fs_obj_list=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)

        hosts = self.topology.get_hosts()
        for fs_obj in vol_uuid_dict:
            for host_id in hosts:
                host_obj = hosts[host_id]
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=fs_obj,
                                                                                   volume_uuid=vol_uuid_dict[fs_obj],
                                                                                   validate_nvme_connect=True,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume")

    def run(self):
        hosts = self.topology.get_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            fun_test.test_assert(expression=nvme_device_name,
                                 message="NVMe device found on Host : {}".format(nvme_device_name))
            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj, rw="write",
                                                                                filename="/dev/"+nvme_device_name,
                                                                                verify="md5", do_verify=0,
                                                                                numjobs=2, iodepth=32
                                                                                )
            fun_test.test_assert(expression=traffic_result, message="FIO traffic write result")
            fun_test.log(traffic_result)

            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj, rw="read",
                                                                                filename="/dev/" + nvme_device_name,
                                                                                verify="md5", do_verify=1,
                                                                                numjobs=2, iodepth=32
                                                                                )
            fun_test.test_assert(expression=traffic_result, message="FIO traffic read result")
            fun_test.log(traffic_result)

    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template


class ConfigPeristenceAfterReset(FunTestCase):
    topology = None
    storage_controller_template = None

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

        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.storage_controller_template.verify_dataplane_ip(storage_controller=fs_obj.get_storage_controller(),
                                                                 dut_index=dut_index)

    def run(self):
        hosts = self.topology.get_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            fun_test.test_assert(expression=nvme_device_name,
                                 message="NVMe device found on Host after FS reboot: {}".format(nvme_device_name))

            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj, rw="write",
                                                                                filename="/dev/" + nvme_device_name,
                                                                                verify="md5", do_verify=0,
                                                                                numjobs=2, iodepth=32
                                                                                )
            fun_test.test_assert(expression=traffic_result, message="FIO traffic write result after FS reboot")
            fun_test.log(traffic_result)

            traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj, rw="read",
                                                                                filename="/dev/" + nvme_device_name,
                                                                                verify="md5", do_verify=1,
                                                                                numjobs=2, iodepth=32
                                                                                )
            fun_test.test_assert(expression=traffic_result, message="FIO traffic read result after FS reboot")
            fun_test.log(traffic_result)

    def cleanup(self):
        # self.storage_controller_template.cleanup()
        pass

    def reset_and_health_check(self, fs_obj):
        # fs_obj.reset()
        fun_test.test_assert(expression=self.storage_controller_template.get_health(
            storage_controller=fs_obj.get_storage_controller()),
                             message="{}: API server health".format(fs_obj))


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BltApiStorageTest())
    setup_bringup.add_test_case(ConfigPeristenceAfterReset())
    setup_bringup.run()