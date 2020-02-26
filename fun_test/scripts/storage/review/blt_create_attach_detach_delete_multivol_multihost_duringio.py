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


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):

        format_drives = True
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "format_drives" in job_inputs:
            format_drives = job_inputs["format_drives"]

        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.blt_template = BltVolumeOperationsTemplate(topology=self.topology, api_logging_level=logging.ERROR)
        self.blt_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed,
                                     format_drives=format_drives)
        fun_test.shared_variables["blt_template"] = self.blt_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list

    def cleanup(self):
        fun_test.log("Performing disconnect/detach/delete cleanup as part of script level cleanup")
        self.blt_template.cleanup()
        self.topology.cleanup()


class GenericCreateAttachDetachDelete(FunTestCase):

    def setup(self):

        testcase = self.__class__.__name__

        self.topology = fun_test.shared_variables["topology"]
        self.blt_template = fun_test.shared_variables["blt_template"]
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

        # Fetch testcase numa cpus to be used
        numa_node_to_use = get_device_numa_node(self.hosts[0].instance, self.ethernet_adapter)
        if self.override_numa_node["override"]:
            numa_node_to_use = self.override_numa_node["override_node"]
        for host in self.hosts:
            if host.name.startswith("cab0"):
                host.host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
            else:
                host.host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]

    def run(self):
        self.blt_count = self.blt_per_host if self.shared_volume else self.blt_per_host * len(self.hosts)
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

            self.attach_vol_result = self.blt_template.attach_m_vol_n_host(host_obj_list=self.hosts,
                                                                           fs_obj=self.fs_obj_list[0],
                                                                           volume_uuid_list=self.vol_uuid_list,
                                                                           validate_nvme_connect=False,
                                                                           raw_api_call=True,
                                                                           nvme_io_queues=None,
                                                                           volume_is_shared=self.shared_volume)

            for host in self.hosts:
                host.nvme_connect_info = {}
                for result in self.attach_vol_result[host]:
                    if self.raw_api_call:
                        subsys_nqn = result["data"]["subsys_nqn"]
                        host_nqn = result["data"]["host_nqn"]
                        dataplane_ip = result["data"]["ip"]
                    else:
                        subsys_nqn = result.subsys_nqn
                        host_nqn = result.host_nqn
                        dataplane_ip = result.ip

                    if subsys_nqn not in host.nvme_connect_info:
                        host.nvme_connect_info[subsys_nqn] = []
                    host_nqn_ip = (host_nqn, dataplane_ip)
                    if host_nqn_ip not in host.nvme_connect_info[subsys_nqn]:
                        host.nvme_connect_info[subsys_nqn].append(host_nqn_ip)

            for host in self.hosts:
                for subsys_nqn in host.nvme_connect_info:
                    for host_nqn_ip in host.nvme_connect_info[subsys_nqn]:
                        host_nqn, dataplane_ip = host_nqn_ip
                        fun_test.test_assert(
                            expression=self.blt_template.nvme_connect_from_host(host_obj=host, subsys_nqn=subsys_nqn,
                                                                               host_nqn=host_nqn,
                                                                               dataplane_ip=dataplane_ip),
                            message="NVMe connect from host: {}".format(host.name))
                        nvme_filename = self.blt_template.get_host_nvme_device(host_obj=host, subsys_nqn=subsys_nqn)
                        fun_test.test_assert(expression=nvme_filename,
                                             message="Get NVMe drive from Host {} using lsblk".format(host.name))

                        # Check number of volumes and devices found from hosts
                        # for host in hosts:
                        host.nvme_block_device_list = []
                        nvme_devices = self.blt_template.get_host_nvme_device(host_obj=host)
                        if nvme_devices:
                            if isinstance(nvme_devices, list):
                                host.nvme_block_device_list.extend(nvme_devices)
                            else:
                                current_device = nvme_devices
                                host.nvme_block_device_list.append(current_device)
                        if self.shared_volume:
                            fun_test.test_assert_expected(expected=self.blt_count,
                                                          actual=len(host.nvme_block_device_list),
                                                          message="Check number of nvme block devices found "
                                                          "on host {} matches with attached ".format(host.name))
                        else:
                            fun_test.test_assert_expected(expected=len(self.attach_vol_result[host]),
                                                          actual=len(host.nvme_block_device_list),
                                                          message="Check number of nvme block devices found "
                                                          "on host {} matches with attached ".format(host.name))

            self.fio_io_size = 100 / len(self.hosts)
            thread_id = {}
            end_host_thread = {}
            fio_output = {}
            fio_offset = 1
            fun_test.shared_variables["fio"] = {}
            for index, host in enumerate(self.hosts):
                fio_output[index] = {}
                end_host_thread[index] = host.instance.clone()
                wait_time = len(self.hosts) - index
                if "multiple_jobs" in self.warm_up_fio_cmd_args:
                    warm_up_fio_cmd_args = {}
                    # Adding the allowed CPUs into the fio warmup command
                    fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                    jobs = ""
                    for id, device in enumerate(host.nvme_block_device_list):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)
                    if self.shared_volume:
                        offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                        size = " --size={}%".format(self.fio_io_size)
                        warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                            fio_cpus_allowed_args + offset + size + jobs
                    else:
                        size = " --size=10%"
                        warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                                fio_cpus_allowed_args + size + jobs
                    warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                    thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                     func=fio_parser,
                                                                     arg1=end_host_thread[index],
                                                                     host_index=index,
                                                                     filename="nofile",
                                                                     **warm_up_fio_cmd_args)
                    fio_offset += self.fio_io_size
                    fun_test.sleep("Fio threadzz", seconds=1)

            if self.detach_duringio:
                fun_test.sleep("Wait before disconnect during IO", seconds=10)
                self.cleanupio()
            fun_test.sleep("Fio threads started", 10)
            try:
                for i, host_name in enumerate(self.hosts):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    if not fun_test.shared_variables["fio"][i] and self.detach_duringio:
                        fun_test.test_assert(True, message="FIO interrupted due to disconnect")
                    else:
                        fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                             "FIO randwrite test with verify in host {}".
                                             format(host_name.name))
                    fio_output[i] = fun_test.shared_variables["fio"][i]

            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from host {}:\n {}".format(host_name, fio_output[i]))

            if not self.detach_duringio:
                self.cleanupio()
            fun_test.test_assert(expression=True, message="Test completed {} Iteration".format(count + 1))

    def cleanupio(self):
        for host_obj in self.hosts:
            host_handle = host_obj.instance
            for subsys_nqn in host_obj.nvme_connect_info:
                status = host_handle.nvme_disconnect(nvme_subsystem=subsys_nqn)
                fun_test.test_assert(expression=status, message="nvme disconnect successful from host {}".format(host_handle))
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                for port in get_volume_result["data"][volume]["ports"]:
                    detach_volume = None
                    try:
                        detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    except ApiException as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    detach_result = False
                    if detach_volume:
                        detach_result = detach_volume.status
                    fun_test.test_assert(expression=detach_volume.status,
                                         message="Detach Volume {} from host with host_nqn {}".format(
                                             volume, get_volume_result["data"][volume]['ports'][port]['host_nqn']))
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


class CreateAttachDetachDeleteMultivolMultihost(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create, attach, connect, disconnect, detach & delete N different volumes "
                                      "attached to M hosts with IO",
                              test_rail_case_ids=["T31394"],
                              steps='''
                                    1. Create 48 volumes
                                    2. Attach 8 volume to 6 hosts
                                    3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                                    4. Let IO complete, then perform nvme disconnect during I/O on all hosts
                                    5. Detach and delete the volumes
                                    6. Continue this in a loop for 24 times  
                              ''')

        def setup(self):
            super(CreateAttachDetachDeleteMultivolMultihost, self).setup()

        def run(self):
            super(CreateAttachDetachDeleteMultivolMultihost, self).run()

        def cleanup(self):
            super(CreateAttachDetachDeleteMultivolMultihost, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostDuringIO(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=2,
            summary="Create,attach,connect,disconnect,detach & delete N different volumes attached to M hosts along "
                    "with active IO during disconnect & detach",
            test_rail_case_ids=["T31395"],
            steps='''
                1. Create 48 volumes
                2. Attach 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO run for 30sec, then perform nvme disconnect during I/O on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIO, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIO, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIO, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostShared(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=3,
            summary="Create,attach,connect,disconnect,detach & delete same N volumes attached to M hosts with IO",
            test_rail_case_ids=["T31397"],
            steps='''
                1. Create 8 volumes
                2. Attach same 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO complete, then perform nvme disconnect on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostShared, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostShared, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostShared, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostSharedDuringIO(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=4,
            summary="Create,attach,connect,disconnect,detach & delete same N volumes attached to M hosts along with "
                    "active IO during disconnect & detach",
            test_rail_case_ids=["T31398"],
            steps='''
                1. Create 8 volumes
                2. Attach 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO run for 30sec, then perform nvme disconnect during I/O on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIO, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIO, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIO, self).cleanup()

class CreateAttachDetachDeleteMultivolMultihostEncrypt(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Create, attach, connect, disconnect, detach & delete N different volumes "
                                      "attached to M hosts with IO",
                              steps='''
                                    1. Create 48 volumes
                                    2. Attach 8 volume to 6 hosts
                                    3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                                    4. Let IO complete, then perform nvme disconnect during I/O on all hosts
                                    5. Detach and delete the volumes
                                    6. Continue this in a loop for 24 times  
                              ''')

        def setup(self):
            super(CreateAttachDetachDeleteMultivolMultihostEncrypt, self).setup()

        def run(self):
            super(CreateAttachDetachDeleteMultivolMultihostEncrypt, self).run()

        def cleanup(self):
            super(CreateAttachDetachDeleteMultivolMultihostEncrypt, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostDuringIOEncrypt(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=6,
            summary="Create,attach,connect,disconnect,detach & delete N different volumes attached to M hosts along "
                    "with active IO during disconnect & detach",
            steps='''
                1. Create 48 volumes
                2. Attach 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO run for 30sec, then perform nvme disconnect during I/O on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIOEncrypt, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIOEncrypt, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostDuringIOEncrypt, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostSharedEncrypt(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=7,
            summary="Create,attach,connect,disconnect,detach & delete same N volumes attached to M hosts with IO",
            steps='''
                1. Create 8 volumes
                2. Attach same 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO complete, then perform nvme disconnect on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedEncrypt, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedEncrypt, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedEncrypt, self).cleanup()


class CreateAttachDetachDeleteMultivolMultihostSharedDuringIOEncrypt(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(
            id=8,
            summary="Create,attach,connect,disconnect,detach & delete same N volumes attached to M hosts along with "
                    "active IO during disconnect & detach",
            steps='''
                1. Create 8 volumes
                2. Attach 8 volume to 6 hosts
                3. Run fio ranwrite test with data integrity enabled, iodepth=16 and numjobs=1
                4. Let IO run for 30sec, then perform nvme disconnect during I/O on all hosts
                5. Detach and delete the volumes
                6. Continue this in a loop for 24 times
                ''')

    def setup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIOEncrypt, self).setup()

    def run(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIOEncrypt, self).run()

    def cleanup(self):
        super(CreateAttachDetachDeleteMultivolMultihostSharedDuringIOEncrypt, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihost())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostDuringIO())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostShared())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostSharedDuringIO())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostEncrypt())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostDuringIOEncrypt())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostSharedEncrypt())
    setup_bringup.add_test_case(CreateAttachDetachDeleteMultivolMultihostSharedDuringIOEncrypt())
    setup_bringup.run()
