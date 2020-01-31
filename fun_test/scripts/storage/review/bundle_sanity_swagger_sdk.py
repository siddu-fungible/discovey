from lib.system.fun_test import *
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.review.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes


def fio_integrity_check(host_obj, filename, job_name="Fungible_nvmeof", numjobs=1, iodepth=1,
                        runtime=60, bs="4k", ioengine="libaio", direct="1",
                        time_based=True, norandommap=True, verify="md5", verify_fatal=1,
                        offset="0kb", verify_state_save=1, verify_dump=1, output="test_integrity",
                        verify_state_load=1, only_read=False):
    host_linux_handle = host_obj.get_instance()
    host_linux_handle.command("cd ~; rm -fr test_fio_with_integrity;"
                              "mkdir test_fio_with_integrity; cd test_fio_with_integrity")
    if not only_read:
        fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw="write",
                                           filename=filename, runtime=runtime, ioengine=ioengine, direct=direct,
                                           timeout=runtime + 15, time_based=time_based,
                                           verify=verify, verify_fatal=verify_fatal, offset=offset,
                                           verify_state_save=verify_state_save, verify_dump=verify_dump)
        fun_test.test_assert(expression=fio_result, message="Write FIO test")

    host_linux_handle.command("cd ~/test_fio_with_integrity;")
    fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw="read",
                                       filename=filename, runtime=runtime, ioengine=ioengine, direct=direct,
                                       timeout=runtime + 15, time_based=time_based, offset=offset,
                                       verify=verify, do_verify=1, verify_fatal=verify_fatal,
                                       verify_state_load=verify_state_load, verify_dump=verify_dump)
    fun_test.test_assert(expression=fio_result, message="Read FIO result")


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
            fio_integrity_check(host_obj=host_obj, filename="/dev/"+nvme_device_name, numjobs=1, iodepth=32)

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
        fun_test.sleep(message="Waiting before firing Dataplane IP commands", seconds=60)
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

            fio_integrity_check(host_obj=host_obj, filename="/dev/"+nvme_device_name, numjobs=1, iodepth=32,
                                only_read=True)

    def cleanup(self):
        # self.storage_controller_template.cleanup()
        pass

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset()
        fs_obj.come.ensure_expected_containers_running()
        fun_test.test_assert(expression=self.storage_controller_template.get_health(
            storage_controller=fs_obj.get_storage_controller()),
                             message="{}: API server health".format(fs_obj))


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BltApiStorageTest())
    setup_bringup.add_test_case(ConfigPeristenceAfterReset())
    setup_bringup.run()
