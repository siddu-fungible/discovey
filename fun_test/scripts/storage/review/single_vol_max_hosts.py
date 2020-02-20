from lib.system.fun_test import *
from lib.system import utils
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from swagger_client.models.body_volume_attach import BodyVolumeAttach
from swagger_client.models.transport import Transport
from swagger_client.rest import ApiException
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *

import string, random
from collections import OrderedDict, Counter


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def get_num_of_tcp_connections(host_obj):
    #netstat_data = host_obj.instance.netstat([4420])
    try:
        output = host_obj.instance.sudo_command("netstat -nalp | grep 4420 | wc -l")
        output = output.split('\r')[0]
        connections = int(output)
    except Exception:
        fun_test.test_assert(False, message="Get netstat info from the host ")
        return None
    return connections

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

        '''
        self = single_fs_setup(self, set_dataplane_ips=False)

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        
        '''

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.blt_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.blt_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed)
        fun_test.shared_variables["blt_template"] = self.blt_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list

        # self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        '''
        fun_test.shared_variables["fs_obj_list"] = fs_obj_list
        hosts = self.topology.get_available_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_list = self.storage_controller_template.get_nvme_namespaces(host_handle=host_handle)
            for ns in nvme_list:
                dev=ns[:-2]
                host_handle.sudo_command("nvme disconnect -d /dev/{}".format(dev))
        '''

    def cleanup(self):

        self.blt_template.cleanup()
        self.topology.cleanup()


class SingleVolumeMaxHosts(FunTestCase):

    def describe(self):

        self.set_test_details(id=1,
                              summary="Max hosts attached to one raw volume",
                              steps='''
                              1. Create a BLT Volume using API Calls
                              2. Attach Volume to the hosts with different host_nqn's
                              3. Nvme connect from hosts and check for tcp connections
                              4. Run fio from the physical hosts to the volume
                              ''')

    def setup(self):

        testcase = self.__class__.__name__

        self.topology = fun_test.shared_variables["topology"]
        self.blt_template = fun_test.shared_variables["blt_template"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        #tc_config = True
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
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "num_hosts" in job_inputs:
            self.num_host = job_inputs["num_hosts"]
        if "num_of_vhosts" in job_inputs:
            self.num_of_vhosts = job_inputs["num_of_vhosts"]

        """
        self.topology = fun_test.shared_variables["topology"]
        self.fs_objs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1_objs = fun_test.shared_variables["f1_objs"]
        self.sc_objs = fun_test.shared_variables["sc_obj"]
        self.f1_ips = fun_test.shared_variables["f1_ips"]
        self.host_info = fun_test.shared_variables["host_info"]
        """

        self.vol_uuid_list = []
        fun_test.shared_variables["blt_count"] = self.blt_count
        vol_type = VolumeTypes().LOCAL_THIN
        
        self.hosts = self.topology.get_available_host_instances()

        suffix = utils.generate_uuid(length=4)
        body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix, vol_type=vol_type,
                                                           capacity=self.capacity, compression_effort=False,
                                                           encrypt=False, data_protection={})
        self.vol_uuid = self.blt_template.create_volume(self.fs_obj_list, body_volume_intent_create)
        fun_test.test_assert(expression=self.vol_uuid[0],
                             message="Volume creation successful with uuid {}".format(self.vol_uuid[0]))

    def run(self):
        self.vhosts_per_host = self.num_of_vhosts / self.num_host
        self.host_nvme_device_dict = {}
        for host_obj in self.hosts:
            self.host_nvme_device_dict[host_obj]=[]
            host_ip = host_obj.get_test_interface(index=0).ip.split('/')[0]
            for i in range(1, self.vhosts_per_host+1):
                host_nqn = "nqn{}.2015-09.com.Fungible:{}".format(i, host_ip)
                vol_uuid = self.vol_uuid[0]

                attach_vol_result = self.attach_volume(self.fs_obj_list[0], vol_uuid, host_obj, host_nqn,
                                                       validate_nvme_connect=True, raw_api_call=True)

                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

        # Populating the NVMe devices available to the hosts

        for host in self.hosts:
            host.nvme_block_device_list = []
            host_linux_handle = host.get_instance()
            self.host_nvme_device_dict[host] = self.blt_template.get_nvme_namespaces_by_lsblk(host_linux_handle)
            for namespace in self.host_nvme_device_dict[host]:
                host.nvme_block_device_list.append("/dev/{}".format(namespace))
            fun_test.log("Available NVMe devices: {}".format(host.nvme_block_device_list))
            # fun_test.test_assert_expected(expected=self.vhosts_per_host,
            #                               actual=len(host.nvme_block_device_list),
            #                               message="Expected NVMe devices are available on {}".format(host.name))
            host.nvme_block_device_list.sort()
            #host.fio_filename = ":".join(host.nvme_block_device_list)

        numa_node_to_use = get_device_numa_node(self.hosts[0].instance, self.ethernet_adapter)
        if self.override_numa_node["override"]:
            numa_node_to_use = self.override_numa_node["override_node"]
        for host in self.hosts:
            if host.name.startswith("cab0"):
                host.host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
            else:
                host.host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]

        fun_test.shared_variables["host_info"] = self.hosts
        fun_test.log("Hosts info: {}".format(dir(self.hosts)))


        #self.fio_io_size = 100 / len(self.hosts)
        self.fio_io_size = 100
        # self.offsets = ["1%", "26%", "51%", "76%"]

        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        #fio_offset = 1

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                         "provided")
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
                # offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                size = " --size={}%".format(self.fio_io_size)
                warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args  + size + jobs
                warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)
                #fio_offset += self.fio_io_size
                fun_test.sleep("Fio threadzz", seconds=1)

        fun_test.sleep("Fio threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO randwrite test with IO depth 16 in host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from host {}:\n {}".format(host.name, fio_output[i]))

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO randwrite test with IO depth 16 in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        for op, stats in aggr_fio_output.items():
            for field, value in stats.items():
                if field == "iops":
                    aggr_fio_output[op][field] = int(round(value))
                if field == "bw":
                    # Converting the KBps to MBps
                    aggr_fio_output[op][field] = int(round(value / 1000))
                if "latency" in field:
                    aggr_fio_output[op][field] = int(round(value) / len(self.hosts))
                # Converting the runtime from milliseconds to seconds and taking the average out of it
                if field == "runtime":
                    aggr_fio_output[op][field] = int(round(value / 1000) / len(self.hosts))

        fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

    def attach_volume(self, fs_obj, volume_uuid, host_obj, host_nqn, validate_nvme_connect=True, raw_api_call=False,
                      nvme_io_queues=None):

        """
        :param fs_obj: fs_object from topology
        :param volume_uuid: uuid of volume returned after creating volume
        :param host_obj: host handle or list of host handles from topology to which the volume needs to be attached
        :param host_nqn: host nqn needed during the attach
        :param validate_nvme_connect: Use this flag to do NVMe connect from host along with attaching volume
        :param raw_api_call: Temporary workaround to use raw API call until swagger APi issues are resolved.
        :return: Attach volume result in case of 1 host_obj
                 If multiple host_obj are provided, the result is a list of attach operation results,
                 in the same order of host_obj
        """
        result_list = []
        host_obj_list = []
        if not isinstance(host_obj, list):
            host_obj_list.append(host_obj)
        else:
            host_obj_list = host_obj
        for host_obj in host_obj_list:
            fun_test.add_checkpoint(checkpoint="Attaching volume %s to host %s" % (volume_uuid, host_obj.name))
            storage_controller = fs_obj.get_storage_controller()
            host_data_ip = host_obj.get_test_interface(index=0).ip.split('/')[0]
            if not raw_api_call:
                attach_fields = BodyVolumeAttach(transport=Transport().TCP,
                                                 host_nqn=host_nqn)

                try:
                    result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                                          body_volume_attach=attach_fields)
                    result_list.append(result)
                except ApiException as e:
                    fun_test.test_assert(expression=False,
                                         message="Exception when attach volume on fs %s: %s\n" % (fs_obj, e))
                    result = None
            else:
                raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
                result = raw_sc_api.volume_attach_remote(vol_uuid=volume_uuid,
                                                         host_nqn=host_nqn)
                result_list.append(result)
            if validate_nvme_connect:
                if raw_api_call:
                    fun_test.test_assert(expression=result["status"], message="Attach volume result")
                    subsys_nqn = result["data"]["subsys_nqn"]
                    host_nqn = result["data"]["host_nqn"]
                    dataplane_ip = result["data"]["ip"]
                else:
                    subsys_nqn = result.subsys_nqn
                    host_nqn = result.host_nqn
                    dataplane_ip = result.ip

                connections_before_connect = get_num_of_tcp_connections(host_obj)
                #host_linux_handle = host_obj.get_instance()
                #name_spaces_before_connect = self.blt_template.get_nvme_namespaces_by_lsblk(host_linux_handle)
                fun_test.test_assert(expression=self.blt_template.nvme_connect_from_host(host_obj=host_obj,
                                                                                         subsys_nqn=subsys_nqn,
                                                                                         host_nqn=host_nqn,
                                                                                         dataplane_ip=dataplane_ip,
                                                                                         nvme_io_queues=nvme_io_queues),
                                     message="NVMe connect from host: {}".format(host_obj.name))
                connections_after_connect = get_num_of_tcp_connections(host_obj)
                fun_test.test_assert_expected(self.tcp_connections_per_connect,
                                              connections_after_connect - connections_before_connect,
                                              message="Number of new tcp connections created after nvme connect")
                fun_test.log("Number of tcp connections from the host {} are {}".format(host_obj.name,
                                                                                        connections_after_connect))

                if host_obj not in self.blt_template.host_nvme_device:
                    self.blt_template.host_nvme_device[host_obj] = []

        return result_list


    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.blt_template


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(SingleVolumeMaxHosts())
    setup_bringup.run()
