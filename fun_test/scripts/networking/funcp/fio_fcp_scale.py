from lib.system.fun_test import *
from lib.system import utils
from lib.fun.fs import Fs
import re
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.helper import *
import ipaddress
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform


def add_to_data_base(value_dict):
    unit_dict = {
        "iops_unit": PerfUnit.UNIT_OPS,
        "bw_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "latency_avg_unit": PerfUnit.UNIT_USECS,
        "latency_50_unit": PerfUnit.UNIT_USECS,
        "latency_90_unit": PerfUnit.UNIT_USECS,
        "latency_95_unit": PerfUnit.UNIT_USECS,
        "latency_99_unit": PerfUnit.UNIT_USECS,
        "latency_9950_unit": PerfUnit.UNIT_USECS,
        "latency_9999_unit": PerfUnit.UNIT_USECS,
    }

    value_dict["date_time"] = get_data_collection_time()
    value_dict["version"] = fun_test.get_version()
    print "HI there, the version is {}".format(value_dict["version"])
    value_dict["platform"] = FunPlatform.F1
    model_name = "NvmeFcpPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
        print "used generic helper to add an entry"
    except Exception as ex:
        fun_test.critical(str(ex))


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    arg1.command("hostname")
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def get_nvme_device(host_obj):
    nvme_list_raw = host_obj.sudo_command("nvme list -o json")
    if "failed to open" in nvme_list_raw.lower():
        nvme_list_raw = nvme_list_raw + "}"
        temp1 = nvme_list_raw.replace('\n', '')
        temp2 = re.search(r'{.*', temp1).group()
        nvme_list_dict = json.loads(temp2, strict=False)
    else:
        try:
            nvme_list_dict = json.loads(nvme_list_raw)
        except:
            nvme_list_raw = nvme_list_raw + "}"
            nvme_list_dict = json.loads(nvme_list_raw, strict=False)

    nvme_device_list = []
    for device in nvme_list_dict["Devices"]:
        if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"]:
            nvme_device_list.append(device["DevicePath"])
        elif "unknown device" in device["ProductName"].lower() or "null" in device["ProductName"].lower():
            if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
                nvme_device_list.append(device["DevicePath"])
    fio_filename = str(':'.join(nvme_device_list))

    return fio_filename


def get_numa(host_obj):
    device_id = host_obj.lspci(grep_filter="1dad")
    if not device_id:
        device_id = host_obj.lspci(grep_filter="Fungible")
    lspci_verbose_mode = host_obj.lspci(slot=device_id[0]["id"], verbose=True)
    numa_number = lspci_verbose_mode[0]["numa_node"]
    # TODO
    # FIX this...if numa 0 then skip core 0 & its HT
    # if numa_number == 0:
    numa_cores = host_obj.lscpu(grep_filter="node{}".format(numa_number))
    cpu_list = numa_cores.values()[0]
    return cpu_list


def storage_cleanup(storage_obj, command_timeout=5):
    # Clean the controllers
    controller_info = storage_obj.peek("storage/ctrlr/nvme")
    controller_data = controller_info["data"]
    for huid, huvalue in controller_data.iteritems():
        if huid != 7:
            for cntlid, cntvalue in huvalue.iteritems():
                for fnid, fnvalue in cntvalue.iteritems():
                    for key_name, key_value in fnvalue.iteritems():
                        if key_name.lower() == "name spaces":
                            if key_value:
                                volume_nsid_list = []
                                for list_value in key_value:
                                    for prop, value in list_value.iteritems():
                                        if prop.lower() == "uuid":
                                            volume_uuid = value
                                        if prop.lower() == "nsid":
                                            volume_nsid_list.append(value)
                        if key_name.lower() == "controller uuid":
                            if key_value:
                                controller_uuid = key_value
                                for vol_nsid in volume_nsid_list:
                                    command_result = storage_obj.detach_volume_from_controller(
                                        ctrlr_uuid=controller_uuid,
                                        ns_id=vol_nsid,
                                        command_duration=command_timeout)
                                    fun_test.simple_assert(command_result["status"],
                                                           "Detach controller with uuid {} & nsid {}".
                                                           format(controller_uuid, vol_nsid))
                                command_result = storage_obj.delete_controller(ctrlr_uuid=controller_uuid,
                                                                               command_duration=command_timeout)
                                fun_test.simple_assert(command_result["status"],
                                                       "Deleting controller with uuid {}".
                                                       format(controller_uuid))
    for huid, huvalue in controller_data.iteritems():
        if huid == 7:
            for cntlid, cntvalue in huvalue.iteritems():
                for fnid, fnvalue in cntvalue.iteritems():
                    for key_name, key_value in fnvalue.iteritems():
                        if key_name.lower() == "name spaces":
                            if key_value:
                                volume_nsid_list = []
                                for list_value in key_value:
                                    for prop, value in list_value.iteritems():
                                        if prop.lower() == "uuid":
                                            volume_uuid = value
                                        if prop.lower() == "nsid":
                                            volume_nsid_list.append(value)
                        if key_name.lower() == "controller uuid":
                            if key_value:
                                controller_uuid = key_value
                                for vol_nsid in volume_nsid_list:
                                    command_result = storage_obj.detach_volume_from_controller(
                                        ctrlr_uuid=controller_uuid,
                                        ns_id=vol_nsid,
                                        command_duration=command_timeout)
                                    fun_test.simple_assert(command_result["status"],
                                                           "Detach controller with uuid {} & nsid {}".
                                                           format(controller_uuid, vol_nsid))
                                command_result = storage_obj.delete_controller(ctrlr_uuid=controller_uuid,
                                                                               command_duration=command_timeout)
                                fun_test.simple_assert(command_result["status"],
                                                       "Deleting controller with uuid {}".
                                                       format(controller_uuid))

    # Clean the volumes
    volume_info = storage_obj.peek("storage/volumes")
    volume_data = volume_info["data"]
    for vol_type, vol_data in volume_data.iteritems():
        if vol_type != "VOL_TYPE_BLK_LOCAL_THIN":
            for vol_uuid, vol_stats in vol_data.iteritems():
                if vol_stats:
                    command_result = storage_obj.delete_volume(type=vol_type, uuid=vol_uuid,
                                                               command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "Deleting volume of type {} with uuid {}".
                                           format(vol_type, vol_uuid))

    for vol_type, vol_data in volume_data.iteritems():
        if vol_type == "VOL_TYPE_BLK_LOCAL_THIN":
            for vol_uuid, vol_stats in vol_data.iteritems():
                if vol_uuid == "drives":
                    pass
                else:
                    if vol_stats:
                        command_result = storage_obj.delete_volume(type=vol_type, uuid=vol_uuid,
                                                                   command_duration=command_timeout)
                        fun_test.simple_assert(command_result["status"], "Deleting volume of type {} with uuid {}".
                                               format(vol_type, vol_uuid))
    storage_obj.disconnect()


class BLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        fun_test.shared_variables["fio"] = {}
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
            fun_test.log("Provided job inputs: {}".format(job_inputs))
            # fun_test.test_assert(False, "No inputs given")
        if "deploy_vol" in job_inputs:
            deploy_vol = job_inputs["deploy_vol"]
        else:
            deploy_vol = True
        if "skip_ctrlr_creation" in job_inputs:
            skip_ctrlr_creation = job_inputs["skip_ctrlr_creation"]
        else:
            skip_ctrlr_creation = False
        if "ipconfig" in job_inputs:
            ipconfig = job_inputs["ipconfig"]
        else:
            ipconfig = True
        if "skip_precondition" in job_inputs:
            skip_precondition = job_inputs["skip_precondition"]
        else:
            skip_precondition = True
        if "storage_fs" in job_inputs:
            fun_test.shared_variables["storage_fs"] = job_inputs["storage_fs"].split(",")
        else:
            fun_test.shared_variables["storage_fs"] = ["fs-67"]
        if "fio_clients" in job_inputs:
            fun_test.shared_variables["fio_clients"] = job_inputs["fio_clients"]
        else:
            fun_test.shared_variables["fio_clients"] = None
        if "server_fs" in job_inputs:
            fun_test.shared_variables["server_fs"] = job_inputs["server_fs"]
        else:
            fun_test.shared_variables["server_fs"] = ["fs-8"]
        if "num_vols" in job_inputs:
            fun_test.shared_variables["num_vols"] = job_inputs["num_vols"]
        else:
            fun_test.shared_variables["num_vols"] = 1
        if "num_servers" in job_inputs:
            fun_test.shared_variables["num_servers"] = job_inputs["num_servers"]
        else:
            fun_test.test_assert(False, "Provide number of servers for test")
        if "cleanup" in job_inputs:
            fun_test.shared_variables["cleanup"] = job_inputs["cleanup"]
        else:
            fun_test.shared_variables["cleanup"] = False
        if "cleanup_blt" in job_inputs:
            fun_test.shared_variables["cleanup_blt"] = job_inputs["cleanup_blt"]
        else:
            fun_test.shared_variables["cleanup_blt"] = False

        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/testbed_inputs.json')

        ##################################
        #  Get Host list connected to FS #
        ##################################
        host_count = 0
        host_list = []
        if fun_test.shared_variables["fio_clients"] is None:
            for fs in fun_test.shared_variables["server_fs"]:
                fs_host_info = testbed_info['fs']['fs-fcp-scale'][fs]['hu_host_list']
                for host in fs_host_info:
                    for key, value in host.items():
                        if value != "x4":
                            host_list.append(key)
                            host_count += 1
                            if host_count == fun_test.shared_variables["num_servers"]:
                                break
            print "The len is {}".format(len(host_list))
            print host_list
            if len(host_list) > fun_test.shared_variables["num_servers"]:
                pop_count = len(host_list) - fun_test.shared_variables["num_servers"]
                for x in range(0, pop_count):
                    host_list.pop()
            elif len(host_list) < fun_test.shared_variables["num_servers"]:
                fun_test.test_assert(False, "Number of hosts available is lesser than requested from user")
        else:
            host_list = fun_test.shared_variables["fio_clients"].split(",")

        hosts_dict = {}
        # Create linux_obj, get nvme device name
        for hosts in host_list:
            hosts_dict[hosts] = {}
            hosts_dict[hosts]["handle"] = Linux(host_ip=hosts, ssh_username="localadmin", ssh_password="Precious1*")
            hosts_dict[hosts]["handle"].install_package("fio")
            hosts_dict[hosts]["handle"].install_package("libaio-dev")
            hosts_dict[hosts]["handle"].sudo_command("iptables -F && ip6tables -F")
            hosts_dict[hosts]["handle"].sudo_command("/etc/init.d/irqbalance stop")
            if skip_ctrlr_creation:
                hosts_dict[hosts]["nvme_device"] = get_nvme_device(hosts_dict[hosts]["handle"])
                fun_test.simple_assert(hosts_dict[hosts]["nvme_device"], "NVMe device on {}".format(hosts))
            hosts_dict[hosts]["cpu_list"] = get_numa(hosts_dict[hosts]["handle"])
            hosts_dict[hosts]["hu_int_name"] = hosts_dict[hosts]["handle"].command(
                "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | head -1 | tr -d :").strip()
            hosts_dict[hosts]["hu_int_ip"] = hosts_dict[hosts]["handle"].command(
                "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(
                    hosts_dict[hosts]["hu_int_name"])).strip()
            hosts_dict[hosts]["handle"].disconnect()

        fun_test.shared_variables["host_list"] = host_list
        fun_test.shared_variables["hosts_dict"] = hosts_dict

        target_f10_storage_obj = {}
        target_f11_storage_obj = {}
        f10_storage_loop_ip = {}
        f11_storage_loop_ip = {}


        # Setup controller and volumes on all storage FS
        for storage_fs in fun_test.shared_variables["storage_fs"]:
            fun_test.log(" ### Configuring FS {} ####".format(storage_fs))
            fun_test.shared_variables[storage_fs] = {}


            storage_fs_come = storage_fs.replace("-", "") + "-come"
            storage_fs_come_obj = Linux(host_ip=storage_fs_come, ssh_username="fun", ssh_password="123")
            target_f10_storage_obj[storage_fs] = StorageController(target_ip=storage_fs_come, target_port=42220)
            target_f11_storage_obj[storage_fs] = StorageController(target_ip=storage_fs_come, target_port=42221)

            fun_test.shared_variables[storage_fs]["target_f10_storage_obj"] = target_f10_storage_obj[storage_fs]
            fun_test.shared_variables[storage_fs]["target_f11_storage_obj"] = target_f11_storage_obj[storage_fs]

            # Get loop back IP:
            # f10_storage_loop_ip = storage_fs_come_obj.command("docker exec -it F1-0 ifconfig lo:0 | "
            #                                                   "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f10_storage_loop_ip[storage_fs] = storage_fs_come_obj.command("docker exec -it F1-0 ifconfig vlan1 | "
                                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f10_storage_loop_ip[storage_fs] = f10_storage_loop_ip[storage_fs].strip()
            storage_fs_come_obj.disconnect()

            # f11_storage_loop_ip = storage_fs_come_obj.command("docker exec -it F1-1 ifconfig lo:0 | "
            #                                                   "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f11_storage_loop_ip[storage_fs] = storage_fs_come_obj.command("docker exec -it F1-1 ifconfig vlan1 | "
                                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f11_storage_loop_ip[storage_fs] = f11_storage_loop_ip[storage_fs].strip()
            storage_fs_come_obj.disconnect()

            try:
                ipaddress.ip_address(unicode(f10_storage_loop_ip[storage_fs].strip()))
            except ValueError:
                fun_test.log("F10 loop-back IP {} is not valid".format(f10_storage_loop_ip[storage_fs]))
                fun_test.simple_assert(False, "F10 loop-back IP {} is in wrong format".format(f10_storage_loop_ip[storage_fs]))
            try:
                ipaddress.ip_address(unicode(f11_storage_loop_ip[storage_fs].strip()))
            except ValueError:
                fun_test.log("F11 loop-back IP {} is not valid".format(f11_storage_loop_ip[storage_fs]))
                fun_test.simple_assert(False, "F11 loop-back IP {} is in wrong format".format(f11_storage_loop_ip[storage_fs]))

        # Parse the json file
        # testcase = self.__class__.__name__
        testcase = "GetSetupDetails"
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))
        setup_details = utils.parse_file_to_json(testcase_file)

        for k, v in setup_details[testcase].iteritems():
            setattr(self, k, v)

        ipcfg_port = self.controller_port
        command_timeout = self.command_timeout
        blt_capacity = self.blt_details["capacity"]
        blt_blk_size = self.blt_details["block_size"]
        fabric_transport = unicode(self.transport_type)
        nvme_io_queues = self.nvme_ioq
        f10_ssd_uuid_list = {}
        f11_ssd_uuid_list = {}
        f10_blt_uuid = {}
        f11_blt_uuid = {}

        for storage_fs in fun_test.shared_variables["storage_fs"]:
            fun_test.log(" ### Configuring FS {} ####".format(storage_fs))
            # Create storage listener
            if ipconfig:
                command_result = target_f10_storage_obj[storage_fs].ip_cfg(ip=f10_storage_loop_ip[storage_fs], port=ipcfg_port)
                fun_test.simple_assert(command_result["status"], "IPCFG on F10")

                command_result = target_f11_storage_obj[storage_fs].ip_cfg(ip=f11_storage_loop_ip[storage_fs], port=ipcfg_port)
                fun_test.simple_assert(command_result["status"], "IPCFG on F11")

            if deploy_vol:
                fun_test.log_section("Deploying Volumes")
                # Get number of drives
                f10_ssd_uuid_list[storage_fs] = []
                f11_ssd_uuid_list[storage_fs] = []

                drive_dict = target_f10_storage_obj[storage_fs].peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                         command_duration=command_timeout)
                f10_ssd_uuid_list[storage_fs] = sorted(drive_dict["data"].keys())
                f10_ssd_count = len(f10_ssd_uuid_list)
                print "Total number of SSD's on F10 {}".format(f10_ssd_count)

                drive_dict = target_f11_storage_obj[storage_fs].peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                         command_duration=command_timeout)
                f11_ssd_uuid_list[storage_fs] = sorted(drive_dict["data"].keys())
                f11_ssd_count = len(f11_ssd_uuid_list)
                print "Total number of SSD's on F11 {}".format(f11_ssd_count)


                # Configure volumes on storage_fs
                f10_ssd_count = 1
                f11_ssd_count = 1

                f10_blt_uuid[storage_fs] = {}
                f11_blt_uuid[storage_fs] = {}

                for host in host_list:
                    f10_blt_uuid[storage_fs][host] = []
                    f11_blt_uuid[storage_fs][host] = []
                    for x in range(0, f10_ssd_count):


                        f10_blt_uuid[storage_fs][host].append(utils.generate_uuid())
                        print "F10_blt_uuid " + str(f10_blt_uuid[storage_fs])
                        #print "X is " + str(x) + " UUID is " + str(f10_blt_uuid[storage_fs][x])
                        command_result = target_f10_storage_obj[storage_fs].create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                                          capacity=blt_capacity,
                                                                                          block_size=blt_blk_size,
                                                                                          name="f10_thin_block_" + str(x),
                                                                                          uuid=f10_blt_uuid[storage_fs][host][0],
                                                                                          drive_uuid=f10_ssd_uuid_list[storage_fs][x],
                                                                                          command_duration=command_timeout)
                        fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F10".format(x))
                    for x in range(0, f11_ssd_count):
                        f11_blt_uuid[storage_fs][host].append(utils.generate_uuid())
                        command_result = target_f11_storage_obj[storage_fs].create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                              capacity=blt_capacity,
                                                                              block_size=blt_blk_size,
                                                                              name="f11_thin_block_" + str(x),
                                                                              uuid=f11_blt_uuid[storage_fs][host][0],
                                                                              drive_uuid=f11_ssd_uuid_list[storage_fs][x],
                                                                              command_duration=command_timeout)
                        fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F11".format(x))




        if 0:

            if not deploy_vol and not skip_ctrlr_creation:
                fun_test.log("Volumes not deployed...")
                drive_dict = target_f10_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN",
                                                         command_duration=command_timeout)
                f10_blt_uuid = {}
                count = 1
                for key in drive_dict["data"]:
                    if key != "drives":
                        f10_blt_uuid[count] = key
                        count += 1
                if count == 1:
                    fun_test.test_assert(False, "F1_0 : BLT not found")

                drive_dict = target_f11_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN",
                                                         command_duration=command_timeout)
                if fun_test.shared_variables["num_vols"] > 12:
                    f11_blt_uuid = {}
                    count = 1
                    for key in drive_dict["data"]:
                        if key != "drives":
                            f11_blt_uuid[count] = key
                            count += 1
                    if count == 1:
                        fun_test.test_assert(False, "F1_1 : BLT not found")

        if not skip_ctrlr_creation:

            index = 0
            using_f10 = True
            using_f11 = True
            f1_index = None
            uuid_index = 0
            f10_controller = {}
            f11_controller = {}
            f10_nqn = {}
            f11_nqn = {}
            nsid = 1
            for storage_fs in fun_test.shared_variables["storage_fs"]:
                fun_test.log(" ### Configuring FS {} ####".format(storage_fs))
                for x in host_list:
                    if 0:
                        if index > 11 and using_f11:
                            blt_uuid = {}
                            storage_obj = target_f11_storage_obj
                            using_f11 = False
                            blt_uuid = f11_blt_uuid
                            target_ip = f11_storage_loop_ip
                        elif index <= 11 and using_f10:
                            blt_uuid = {}
                            storage_obj = target_f10_storage_obj
                            using_f10 = False
                            blt_uuid = f10_blt_uuid
                            target_ip = f10_storage_loop_ip
                    f10_controller[storage_fs] = {}
                    f11_controller[storage_fs] = {}
                    f10_nqn[storage_fs] = {}
                    f11_nqn[storage_fs] = {}

                    f10_controller[storage_fs][x] = utils.generate_uuid()
                    f11_controller[storage_fs][x] = utils.generate_uuid()
                    remote_ip = hosts_dict[x]["hu_int_ip"]
                    print "Creating NVMeOF controller to remote {}".format(remote_ip)
                    f10_nqn[storage_fs][x] = "nqn" + str(index)
                    index += 1
                    f11_nqn[storage_fs][x] = "nqn" + str(index)
                    #nqn = "nqn" + str(index)
                    command_result = target_f10_storage_obj[storage_fs].create_controller(ctrlr_uuid=f10_controller[storage_fs][x],
                                                                   transport=fabric_transport.upper(),
                                                                   remote_ip=remote_ip,
                                                                   port=ipcfg_port,
                                                                   nqn=f10_nqn[storage_fs][x],
                                                                   command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "F1-0 Create of fabric controller {} to remote {}".
                                         format(x, remote_ip))

                    command_result = target_f11_storage_obj[storage_fs].create_controller(ctrlr_uuid=f11_controller[storage_fs][x],
                                                                   transport=fabric_transport.upper(),
                                                                   remote_ip=remote_ip,
                                                                   port=ipcfg_port,
                                                                   nqn=f11_nqn[storage_fs][x],
                                                                   command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "F1-1 Create of fabric controller {} to remote {}".
                                         format(x, remote_ip))

                    index += 1
                    print "Storage FS is %s , x is %s , f10_blt_uuid array is %s" %(str(storage_fs),str(x),str(f10_blt_uuid))
                    print "Storage FS is %s , x is %s , f10_blt_uuid array is %s" % (
                    str(storage_fs), str(x), str(f11_blt_uuid))
                    # Attach volumes to the controller
                    command_result = target_f10_storage_obj[storage_fs].attach_volume_to_controller(ctrlr_uuid=f10_controller[storage_fs][x],
                                                                             ns_id=nsid,
                                                                             vol_uuid=f10_blt_uuid[storage_fs][x][0],
                                                                             command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "F1-0 Attach BLT {} to remote {}".
                                         format(uuid_index, remote_ip))

                    nsid += 1

                    command_result = target_f11_storage_obj[storage_fs].attach_volume_to_controller(ctrlr_uuid=f11_controller[storage_fs][x],
                                                                             ns_id=nsid,
                                                                             vol_uuid=f11_blt_uuid[storage_fs][x][0],
                                                                             command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "F1-1 Attach BLT {} to remote {}".
                                         format(uuid_index, remote_ip))
                    nsid += 1
                    uuid_index += 1

                    # NMVe connect from x86 server to FS
                    hosts_dict[x]["handle"].modprobe("nvme_tcp")
                    check_nvmetcp = hosts_dict[x]["handle"].lsmod("nvme_tcp")
                    fun_test.sleep("Waiting for load to complete", 2)
                    if not check_nvmetcp:
                        fun_test.critical("nvme_tcp load failed on {}".format(x))
                    hosts_dict[x]["handle"].sudo_command("nvme connect -t {} -n {} -a {} -q {} -i {} -s {}".
                                                         format(fabric_transport.lower(),
                                                                f10_nqn[storage_fs][x],
                                                                f10_storage_loop_ip[storage_fs],
                                                                remote_ip,
                                                                nvme_io_queues,
                                                                ipcfg_port),
                                                         timeout=90)

                    hosts_dict[x]["handle"].sudo_command("nvme connect -t {} -n {} -a {} -q {} -i {} -s {}".
                                                         format(fabric_transport.lower(),
                                                                f11_nqn[storage_fs][x],
                                                                f11_storage_loop_ip[storage_fs],
                                                                remote_ip,
                                                                nvme_io_queues,
                                                                ipcfg_port),
                                                         timeout=90)

                    fun_test.sleep("Waiting for disk to be accessible to host", 5)
                    hosts_dict[x]["nvme_device"] = get_nvme_device(hosts_dict[x]["handle"])
                    if not hosts_dict[x]["nvme_device"]:
                        hosts_dict[x]["handle"].disconnect()
                        fun_test.test_assert(False, "NVMe device not found on {}".format(x))

            #fun_test.shared_variables["fs_controllers"] = f11_controller[storage_fs]
            fun_test.shared_variables["blt_uuid"] = {}
            fun_test.shared_variables["f10_blt_uuid"] = f10_blt_uuid
            if fun_test.shared_variables["num_vols"] > 12:
                fun_test.shared_variables["f11_blt_uuid"] = f11_blt_uuid

        print "F11_nqn : " + str(f11_nqn)
        print "F10_nqn : " + str(f10_nqn)

        for storage_fs in fun_test.shared_variables["storage_fs"]:
            # Disconnect all COMe objects
            target_f10_storage_obj[storage_fs].disconnect()
            target_f11_storage_obj[storage_fs].disconnect()

        ##################################
        #     Run fio from all hosts     #
        ##################################
        if 1:
            if not skip_precondition:
                for precond in range(0, 2):
                    print host_list
                    wait_time = len(host_list)
                    thread_count = 1
                    thread_id = {}
                    fio_output = {}
                    for hosts in hosts_dict:
                        print "Running Pre-condition{} on {}".format(precond, hosts)
                        host_clone = hosts_dict[hosts]["handle"].clone()
                        thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                                func=fio_parser,
                                                                                host_index=thread_count,
                                                                                arg1=host_clone,
                                                                                filename=hosts_dict[hosts]["nvme_device"],
                                                                                rw="write",
                                                                                name="precondition_" + str(hosts),
                                                                                cpus_allowed=hosts_dict[hosts]["cpu_list"],
                                                                                **self.precondition_args)
                        fun_test.sleep("Fio threadzz", seconds=1)
                        wait_time -= 1
                        thread_count += 1
                    fun_test.sleep("Fio threads started", 15)
                    for x in range(1, len(host_list) + 1):
                        try:
                            fun_test.log("Joining fio thread {}".format(x))
                            fun_test.join_thread(fun_test_thread_id=thread_id[x])
                            fun_test.log("FIO Command Output:")
                            fun_test.log(fun_test.shared_variables["fio"][x])
                            fun_test.test_assert(fun_test.shared_variables["fio"][x], "Fio threaded test")
                            fio_output[x] = {}
                            fio_output[x] = fun_test.shared_variables["fio"][x]
                        except Exception as ex:
                            fun_test.critical(str(ex))
                            fun_test.log("FIO Command Output for volume {}:\n {}".format(x, fio_output[x]))

            fun_test.sleep("Pre-condition done", 10)

    def cleanup(self):
        # Cleanup the NVMe setup
        if fun_test.shared_variables["cleanup"]:
            hosts_dict = fun_test.shared_variables["hosts_dict"]
            host_len = len(fun_test.shared_variables["host_list"])
            #target_f10_storage_obj = fun_test.shared_variables["target_f10_storage_obj"]
            #target_f11_storage_obj = fun_test.shared_variables["target_f11_storage_obj"]
            #using_f10 = True
            #using_f11 = True

            for host in fun_test.shared_variables["host_list"]:
                try:
                    nvme_device = hosts_dict[host]["nvme_device"]
                    if ":" in nvme_device:
                        nvme_device_list = nvme_device.split(":")
                        for nvme_dev in nvme_device_list:
                            temp = nvme_dev.split("/")[-1]
                            temp1 = re.search('nvme(.[0-9]*)', temp)
                            nvme_disconnect_device = temp1.group()
                            hosts_dict[host]["handle"].sudo_command(
                                "nvme disconnect -d {}".format(nvme_disconnect_device))
                        nvme_dev_output = get_nvme_device(hosts_dict[host]["handle"])
                        if nvme_dev_output:
                            fun_test.critical(False, "NVMe disconnect failed on {}".format(host))
                            hosts_dict[host]["handle"].disconnect()
                    else:
                        temp = nvme_device.split("/")[-1]
                        temp1 = re.search('nvme(.[0-9]*)', temp)
                        nvme_disconnect_device = temp1.group()
                        hosts_dict[host]["handle"].sudo_command("nvme disconnect -d {}".format(nvme_disconnect_device))
                        nvme_dev_output = get_nvme_device(hosts_dict[host]["handle"])
                        if nvme_dev_output:
                            fun_test.critical(False, "NVMe disconnect failed on {}".format(host))
                            hosts_dict[host]["handle"].disconnect()
                except:
                    pass

            for storage_fs in fun_test.shared_variables["storage_fs"]:
                for storage_obj in [fun_test.shared_variables[storage_fs]["target_f10_storage_obj"],fun_test.shared_variables[storage_fs]["target_f11_storage_obj"]]:
                    storage_cleanup(storage_obj)


class BLTVolumePerformanceTestcase(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        pass

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[3:]

        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))
        setup_details = utils.parse_file_to_json(testcase_file)

        for k, v in setup_details[testcase].iteritems():
            setattr(self, k, v)

        host_list = fun_test.shared_variables["host_list"]
        hosts_dict = fun_test.shared_variables["hosts_dict"]

        table_data_headers = ["Operation", "Block_Size", "Num Vols", "IOPs", "BW in Gbps", "Latency Avg", "Latency 50",
                              "Latency 90", "Latency 95", "Latency 99", "Latency 99.50", "Latency 99.99"]
        table_data_cols = ["operation", "block_size", "num_vols", "total_iops", "total_bw", "latency_avg", "latency_50",
                           "latency_90", "latency_95", "latency_99", "latency_9950", "latency_9999"]

        # Run read fio test from all hosts
        wait_time = len(host_list)
        thread_count = 1
        thread_id = {}
        fio_output = {}
        host_thread_map = {}
        fio_test = self.fio_cmd_args["rw"]
        if "write" in fio_test:
            fio_result_name = "write"
            numjobs_set = True
        elif "read" in fio_test:
            fio_result_name = "read"
        print "Hosts_dict is " + str(hosts_dict)
        one_host = hosts_dict.keys()[0]
        self.fio_cmd_args["numjobs"] = self.fio_cmd_args["numjobs"] * len(hosts_dict[one_host]["nvme_device"].split(':'))
        for hosts in hosts_dict:
            if "write" in fio_test and numjobs_set:
                self.fio_cmd_args["numjobs"] = \
                    self.fio_cmd_args["numjobs"] * len(hosts_dict[hosts]["nvme_device"].split(":"))
                numjobs_set = False
            print "Running {} test on {}".format(fio_test, hosts)
            host_clone = hosts_dict[hosts]["handle"].clone()
            temp = hosts_dict[hosts]["handle"].command("hostname")
            hostname = temp.strip()
            host_thread_map[thread_count] = hostname

            thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                    func=fio_parser,
                                                                    host_index=thread_count,
                                                                    arg1=host_clone,
                                                                    filename=hosts_dict[hosts]["nvme_device"],
                                                                    name=fio_test + "_" + str(hosts),
                                                                    cpus_allowed=hosts_dict[hosts]["cpu_list"],
                                                                    timeout=self.fio_cmd_args["runtime"] * 2,
                                                                    **self.fio_cmd_args)
            fun_test.sleep("Fio threadzz", seconds=1)
            wait_time -= 1
            thread_count += 1
        fun_test.sleep("Fio threads started", 10)
        iops_sum = 0
        bw_sum = 0
        for x in range(1, len(host_list) + 1):
            try:
                fun_test.log("Joining fio thread {}".format(x))
                fun_test.join_thread(fun_test_thread_id=thread_id[x])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][x])
                fun_test.test_assert(fun_test.shared_variables["fio"][x], "Fio threaded test")
                fio_output[x] = {}
                fio_output[x] = fun_test.shared_variables["fio"][x]
                iops_sum += fio_output[x][fio_result_name]["iops"]
                bw_sum += fio_output[x][fio_result_name]["bw"]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output for volume {}:\n {}".format(x, fio_output[x]))
        for hosts in hosts_dict:
            hosts_dict[hosts]["handle"].disconnect()
        print "******************************************************"
        print "Collective {} test IOP's is {}".format(fio_test, iops_sum)
        print "******************************************************"
        print fun_test.shared_variables["fio"]
        # Check which host is giving highest latency50 and use that to plot latency
        fio_latency = fun_test.shared_variables["fio"]
        max_lat = 0
        for thread, value in fio_latency.iteritems():
            if value[fio_result_name]["latency50"] > max_lat:
                max_lat = value[fio_result_name]["latency50"]
                host_thread = thread
                print "The max is {}".format(max_lat)
                print "The host is {}".format(host_thread_map[host_thread])
        print "The final max is {}".format(max_lat)
        print "The final host is {}".format(host_thread_map[host_thread])
        result_dict = fun_test.shared_variables["fio"][host_thread][fio_result_name]
        print result_dict
        operation = fio_test
        block_size = self.fio_cmd_args["bs"]
        num_vols = fun_test.shared_variables["num_vols"]
        total_iops = int(round(iops_sum))
        total_bw = bw_sum/125000
        latency_avg = result_dict["clatency"]
        latency_50 = result_dict["latency50"]
        latency_90 = result_dict["latency90"]
        latency_95 = result_dict["latency95"]
        latency_99 = result_dict["latency99"]
        latency_9950 = result_dict["latency9950"]
        latency_9999 = result_dict["latency9999"]
        row_data_list = []
        table_data_rows = []
        for item in table_data_cols:
            row_data_list.append(eval(item))
        table_data_rows.append(row_data_list)
        value_dict = {
            "test_case": "NVMe/TCP",
            "volumes": num_vols,
            "operation": fio_test,
            "{}_block_size".format(fio_result_name): block_size,
            "{}_iops".format(fio_result_name): total_iops,
            "{}_bw".format(fio_result_name): total_bw,
            "{}_latency_avg".format(fio_result_name): latency_avg,
            "{}_latency_50".format(fio_result_name): latency_50,
            "{}_latency_90".format(fio_result_name): latency_90,
            "{}_latency_95".format(fio_result_name): latency_95,
            "{}_latency_99".format(fio_result_name): latency_99,
            "{}_latency_9950".format(fio_result_name): latency_9950,
            "{}_latency_9999".format(fio_result_name): latency_9999}
        # add_to_data_base(value_dict)
        print value_dict
        table_data = {"headers": table_data_headers, "rows": table_data_rows}

        fun_test.add_table(panel_header="NVMe FunTCP FCP {} Perf".format(fio_test).upper(),
                           table_name=self.summary,
                           table_data=table_data)

    def cleanup(self):
        pass


class BLTFioRandWrite(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Write performance of BLT volume over NVMe FunTCP FCP",
                              steps=''' ''')


class BLTFioRandRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance of BLT volume over NVMe FunTCP FCP",
                              steps='''''')


if __name__ == '__main__':
    ts = BLTVolumePerformanceScript()
    ts.add_test_case(BLTFioRandWrite())
    ts.add_test_case(BLTFioRandRead())
    ts.run()
