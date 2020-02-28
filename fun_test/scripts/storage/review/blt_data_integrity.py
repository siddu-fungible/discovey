#Owner: Babu Chimmi
from lib.system.fun_test import *
fun_test.enable_storage_api()
from lib.third_party.swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from lib.third_party.swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import StorageControllerApi
from scripts.storage.storage_helper import *


class BringupSetup(FunTestScript):
    topology = None

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        already_deployed = False
        format_drives = True
        if "already_deployed" in job_inputs:
            already_deployed = job_inputs["already_deployed"]
        if already_deployed:
            format_drives = False
        if "format_drives" in job_inputs:
            format_drives = job_inputs["format_drives"]

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template
        self.storage_controller_template.initialize(already_deployed=already_deployed, dpu_indexes=[0],
                                                    format_drives=format_drives)

    def cleanup(self):
        self.topology.cleanup()  # except bundle, dp IP address, mainly collects logs


class BaseBltDataIntegrity(FunTestCase):
    topology = None
    storage_controller_template = None

    def setup(self,):

        self.testcase = self.__class__.__name__
        job_inputs = fun_test.get_job_inputs()
        capacity = int(16*1024*1024*1024)
        # capacity = 1600143753216 - 3*4096
        if "capacity" in job_inputs:
            capacity = job_inputs["capacity"]

        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        self.name = 1
        vol_type = VolumeTypes().LOCAL_THIN

        body_volume_intent_create = BodyVolumeIntentCreate(name="blt_vol"+str(self.name), vol_type=vol_type,
                                                           capacity=capacity, encrypt=self.encrypt, data_protection={})

        self.fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)
        # creates volume on all available FS's list
        self.vol_base_uuid_list = self.storage_controller_template.create_volume(fs_obj=self.fs_obj_list,
                                                                                 body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=self.vol_base_uuid_list, message="Created BLT Volume {} with capacity {} "
                                                                         "bytes".format(self.vol_base_uuid_list,
                                                                                        capacity))
        self.hosts = self.topology.get_available_host_instances()

        attach_vol_result = self.storage_controller_template.attach_volume(host_obj=self.hosts,
                                                                           fs_obj=self.fs_obj_list[0],
                                                                           volume_uuid=self.vol_base_uuid_list[0],
                                                                           validate_nvme_connect=True,
                                                                           raw_api_call=True)
        fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

        # # Populating the NVMe devices available to the hosts

        for host in self.hosts:
            nvme_device_name = self.storage_controller_template._get_fungible_nvme_namespaces(host_handle=host.instance)
            fun_test.log("Available NVMe devices: {}".format(nvme_device_name))
            fun_test.test_assert_expected(expected=1,
                                          actual=len(nvme_device_name),
                                          message="Expected NVMe devices are available")

    def run(self):
        modes = [("write", "read"), ("write", "randread"), ("randwrite", "read"), ("randwrite", "randread")]
        bsizes = ["4k", "8k", "16k", "32k", "64k", "128k", "256k", "512k", "1m", "2m"]
        # # Fetch testcase numa cpus to be used

        for host in self.hosts:
            host_handle = host.instance
            nvme_device_name = self.storage_controller_template._get_fungible_nvme_namespaces(host_handle=host_handle)

            if host.name.startswith("cab0"):
                host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
            else:
                host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][0]

            for wmode, rmode in modes:
                for bsz in bsizes:
                    fio_write_cmd_args = {"ioengine": "libaio", "size": "100%", "rw": wmode, "direct": 1,
                                          "prio": 0, "iodepth": 64, "bs": bsz, "numjobs": 1, "do_verify": 0,
                                          "verify": "md5", "cpus_allowed_policy": "split", "timeout": 3600,
                                          "refill_buffers": "NO_VALUE"}

                    fio_read_cmd_args = {"ioengine": "libaio", "size": "100%", "rw": rmode, "direct": 1,
                                         "prio": 0, "iodepth": 64, "bs": bsz, "numjobs": 1, "do_verify": 1,
                                         "verify": "md5", "cpus_allowed_policy": "split", "timeout": 3600}

                    fio_output = host_handle.pcie_fio(filename=nvme_device_name[0], cpus_allowed=host_numa_cpus,
                                                      **fio_write_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "{}  on the nvme device {} with block size {}".
                                         format(wmode, nvme_device_name[0], bsz))

                    fio_output = host_handle.pcie_fio(filename=nvme_device_name[0], cpus_allowed=host_numa_cpus,
                                                      **fio_read_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "{} on the nvme device {} with block size {}".
                                         format(rmode, nvme_device_name[0], bsz))

    def cleanup(self):
        self.storage_controller_template.cleanup()


class BltDataIntegrity(BaseBltDataIntegrity):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Data integrity in BLT volumes ",
                              test_rail_case_ids=["C36979", "C36980", "C36981", "C36982"],
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a  BLT  Volume using API Call
                              3. Attach the  BLT  Volume using API Call
                              4. Perform FIO tests for various block sizes and read/write operations
                              ''')

    def setup(self):
        self.encrypt = False
        super(BltDataIntegrity, self).setup()


class BltDataIntegrityEncrypt(BaseBltDataIntegrity):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Data integrity in BLT encrypted volumes ",
                              test_rail_case_ids=["C37719", "C37720", "C37721", "C7722"],
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a  BLT encrypted Volume using API Call
                              3. Attach the  BLT  Volume using API Call
                              4. Perform FIO tests for various block sizes and read/write operations
                              ''')

    def setup(self):
        self.encrypt = True
        super(BltDataIntegrityEncrypt, self).setup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BltDataIntegrity())
    setup_bringup.add_test_case(BltDataIntegrityEncrypt())

    setup_bringup.run()
