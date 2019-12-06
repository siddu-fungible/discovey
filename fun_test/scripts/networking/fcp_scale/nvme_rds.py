from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.helper import *
import ipaddress
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform


def add_to_data_base(value_dict):
    unit_dict = {
        "read_avg_latency_unit": PerfUnit.UNIT_USECS,
        "write_avg_latency_unit": PerfUnit.UNIT_USECS,
        "read_min_latency_unit": PerfUnit.UNIT_USECS,
        "write_min_latency_unit": PerfUnit.UNIT_USECS,
        "read_max_latency_unit": PerfUnit.UNIT_USECS,
        "write_max_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_bandwidth_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "write_bandwidth_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "read_msg_rate_unit": PerfUnit.UNIT_MPPS,
        "write_msg_rate_unit": PerfUnit.UNIT_MPPS,
    }

    value_dict["date_time"] = get_data_collection_time()
    value_dict["version"] = fun_test.get_version()
    value_dict["platform"] = FunPlatform.F1
    model_name = "NvmeRdsFcpPerformance"
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
        elif "Unknown Device" in device["ProductName"]:
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


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="FS details")

    def setup(self):
        pass

    def cleanup(self):
        pass


class GetSetupDetails(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):
        fun_test.shared_variables["fio"] = {}

    def run(self):
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
            fun_test.log("Provided job inputs: {}".format(job_inputs))
            fun_test.test_assert(False, "No inputs given")
        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
        else:
            deploy_setup = True
        if "precondition" in job_inputs:
            precondition = job_inputs["precondition"]
        else:
            precondition = True
        if "storage_fs" in job_inputs:
            fun_test.shared_variables["storage_fs"] = job_inputs["storage_fs"]
        else:
            fun_test.shared_variables["storage_fs"] = ["fs-67"]
        if "server_fs" in job_inputs:
            fun_test.shared_variables["server_fs"] = job_inputs["server_fs"]
        else:
            fun_test.shared_variables["server_fs"] = ["fs-8", "fs-38"]
        if "num_vols" in job_inputs:
            fun_test.shared_variables["num_vols"] = job_inputs["num_vols"]
        else:
            fun_test.shared_variables["num_vols"] = 4
        if "num_servers" in job_inputs:
            fun_test.shared_variables["num_servers"] = job_inputs["num_servers"]
        else:
            fun_test.test_assert(False, "Provide number of servers for test")

        # Parse storage_fs inputs
        # TODO use multiple storage_fs

        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/testbed_inputs.json')

        testcase = self.__class__.__name__
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))
        fio_test_args = utils.parse_file_to_json(testcase_file)

        for k, v in fio_test_args[testcase].iteritems():
            setattr(self, k, v)

        if deploy_setup:
            storage_fs_come = fun_test.shared_variables["storage_fs"][0].replace("-", "") + "-come"
            storage_fs_come_obj = Linux(host_ip=storage_fs_come, ssh_username="fun", ssh_password="123")
            target_f10_storage_obj = StorageController(target_ip=storage_fs_come, target_port=42220)
            target_f11_storage_obj = StorageController(target_ip=storage_fs_come, target_port=42221)

            # Get loop back IP:
            f10_storage_loop_ip = storage_fs_come_obj.command("docker exec -it F1-0 ifconfig lo:0 | "
                                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f10_storage_loop_ip = f10_storage_loop_ip.strip()
            storage_fs_come_obj.disconnect()
            f11_storage_loop_ip = storage_fs_come_obj.command("docker exec -it F1-1 ifconfig lo:0 | "
                                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
            f11_storage_loop_ip = f11_storage_loop_ip.strip()
            storage_fs_come_obj.disconnect()
            try:
                ipaddress.ip_address(unicode(f10_storage_loop_ip.strip()))
            except ValueError:
                fun_test.log("F10 loop-back IP {} is not valid".format(f10_storage_loop_ip))
                fun_test.simple_assert(False, "F10 loop-back IP is in wrong format")
            try:
                ipaddress.ip_address(unicode(f11_storage_loop_ip.strip()))
            except ValueError:
                fun_test.log("F11 loop-back IP {} is not valid".format(f11_storage_loop_ip))
                fun_test.simple_assert(False, "F11 loop-back IP is in wrong format")

            # Create storage listener
            ipcfg_port = self.controller_port
            command_timeout = self.command_timeout
            blt_capacity = self.blt_details["capacity"]
            blt_blk_size = self.blt_details["block_size"]

            command_result = target_f10_storage_obj.ip_cfg(ip=f10_storage_loop_ip, port=ipcfg_port)
            fun_test.simple_assert(command_result["status"], "IPCFG on F10")

            command_result = target_f11_storage_obj.ip_cfg(ip=f11_storage_loop_ip, port=ipcfg_port)
            fun_test.simple_assert(command_result["status"], "IPCFG on F11")

            #################################################
            #            Servers connected to FS config     #
            #################################################
            # Configure server connected FS
            fs_server_storage_obj = {}
            num_servers = fun_test.shared_variables["num_servers"]
            for fs in fun_test.shared_variables["server_fs"]:
                print "In server FS"
                fs_name = fs.replace("-", "") + "-come"
                f10_storage_obj = StorageController(target_ip=fs_name, target_port=42220)
                f11_storage_obj = StorageController(target_ip=fs_name, target_port=42221)
                linux_obj = Linux(host_ip=fs_name, ssh_username="fun", ssh_password="123")
                f10_lo_ip = linux_obj.command("docker exec -it F1-0 ifconfig lo:0 | "
                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
                f10_lo_ip = f10_lo_ip.strip()
                f11_lo_ip = linux_obj.command("docker exec -it F1-1 ifconfig lo:0 | "
                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'")
                f11_lo_ip = f11_lo_ip.strip()
                fs_server_storage_obj.update({fs_name: {"f10_obj": f10_storage_obj, "f11_obj": f11_storage_obj,
                                                        "f10_lo": f10_lo_ip, "f11_lo": f11_lo_ip}})

                command_result = f10_storage_obj.ip_cfg(ip=f10_lo_ip, port=ipcfg_port)
                fun_test.simple_assert(command_result["status"], "IPCFG on F10 of {}".format(fs_name))

                command_result = f11_storage_obj.ip_cfg(ip=f11_lo_ip, port=ipcfg_port)
                fun_test.simple_assert(command_result["status"], "IPCFG on F11 of {}".format(fs_name))

            # Get number of drives
            f10_ssd_uuid_list = []
            f11_ssd_uuid_list = []
            drive_dict = target_f10_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                     command_duration=command_timeout)
            f10_ssd_uuid_list = sorted(drive_dict["data"].keys())
            f10_ssd_count = len(f10_ssd_uuid_list)
            print "Total number of SSD's on F10 {}".format(f10_ssd_count)

            drive_dict = target_f11_storage_obj.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                     command_duration=command_timeout)
            f11_ssd_uuid_list = sorted(drive_dict["data"].keys())
            f11_ssd_count = len(f11_ssd_uuid_list)
            print "Total number of SSD's on F11 {}".format(f11_ssd_count)

            total_avail_ssd = f10_ssd_count + f11_ssd_count
            print "Total SSD available : {}".format(total_avail_ssd)
            print "num vol " + str(fun_test.shared_variables["num_vols"])
            print "num server " + str(fun_test.shared_variables["num_servers"])
            fun_test.test_assert(
                expression=(fun_test.shared_variables["num_vols"] == fun_test.shared_variables["num_servers"]),
                message="Volume & server count")

            # Configure volumes on storage_fs
            if f10_ssd_count < fun_test.shared_variables["num_vols"] <= total_avail_ssd:
                f10_blt_uuid = {}
                f11_blt_uuid = {}
                for x in range(0, f10_ssd_count):
                    f10_blt_uuid[x] = utils.generate_uuid()
                    command_result = target_f10_storage_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=blt_capacity,
                                                                          block_size=blt_blk_size,
                                                                          name="f10_thin_block_" + str(x),
                                                                          uuid=f10_blt_uuid[x],
                                                                          drive_uuid=f10_ssd_uuid_list[x],
                                                                          command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F10".format(x))

                diff_ssd_count = total_avail_ssd - f10_ssd_count
                for x in range(0, diff_ssd_count):
                    f11_blt_uuid[x] = utils.generate_uuid()
                    command_result = target_f11_storage_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=blt_capacity,
                                                                          block_size=blt_blk_size,
                                                                          name="f11_thin_block_" + str(x),
                                                                          uuid=f11_blt_uuid[x],
                                                                          drive_uuid=f11_ssd_uuid_list[x],
                                                                          command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F11".format(x))

                # Creating RDS controller on F10
                num_rds_ctrl = num_servers / 2  # 2 controller's per FS
                print "Number of RDS controller is {}".format(num_rds_ctrl)
                f10_rds_ctrl = {}
                f11_rds_ctrl = {}
                index = 0
                fs_server_come_keys = fs_server_storage_obj.keys()
                f1_index = None
                for x in range(0, num_rds_ctrl):
                    print "The index is {}".format(index)
                    if not f1_index:
                        f1_name = "f10_lo"
                        f1_index = True
                    else:
                        f1_name = "f11_lo"
                    f10_rds_ctrl[x] = utils.generate_uuid()
                    command_result = target_f10_storage_obj.create_controller(ctrlr_uuid=f10_rds_ctrl[x],
                                                                              transport="RDS",
                                                                              nqn="nqn" + str(x),
                                                                              port=ipcfg_port,
                                                                              remote_ip=fs_server_storage_obj[
                                                                                  fs_server_come_keys[index]][f1_name],
                                                                              command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "F1_0 : Creation of RDS controller to remote {} : {}".
                                           format(fs_server_come_keys[index], f1_name))
                    if f1_name == "f11_lo":
                        index += 1
                        f1_index = False

                for x in range(0, num_rds_ctrl):
                    if not f1_index:
                        f1_name = "f10_lo"
                        f1_index = True
                    else:
                        f1_name = "f11_lo"
                    f11_rds_ctrl[x] = utils.generate_uuid()
                    command_result = target_f11_storage_obj.create_controller(ctrlr_uuid=f11_rds_ctrl[x],
                                                                              transport="RDS",
                                                                              nqn="nqn" + str(x),
                                                                              port=ipcfg_port,
                                                                              remote_ip=fs_server_storage_obj[
                                                                                  fs_server_come_keys[index]][f1_name],
                                                                              command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "F1_1 : Creation of RDS controller to remote {} : {}".
                                           format(fs_server_come_keys[index], f1_name))

            elif fun_test.shared_variables["num_vols"] > total_avail_ssd:
                print "not configuring"
                fun_test.test_assert(False, "Not configuring!!")
            else:
                print "configuring on F10"
                f10_blt_uuid = {}
                for x in range(0, fun_test.shared_variables["num_vols"]):
                    f10_blt_uuid[x] = utils.generate_uuid()
                    command_result = target_f10_storage_obj.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                          capacity=blt_capacity,
                                                                          block_size=blt_blk_size,
                                                                          name="f10_thin_block_" + str(x),
                                                                          uuid=f10_blt_uuid[x],
                                                                          drive_uuid=f10_ssd_uuid_list[x],
                                                                          command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F10".format(x))

                # Creating RDS controller on F10
                if num_servers == 1:
                    num_rds_ctrl = 1
                else:
                    num_rds_ctrl = num_servers / 2  # 2 controller's per FS
                print "Number of RDS controller is {}".format(num_rds_ctrl)
                f10_rds_ctrl = {}
                index = 0
                fs_server_come_keys = fs_server_storage_obj.keys()
                f1_index = None
                blt_cnt = 0
                nsid = 1
                for x in range(0, num_rds_ctrl):
                    print "The index is {}".format(index)
                    if not f1_index:
                        f1_name = "f10_lo"
                        f1_index = True
                    else:
                        f1_name = "f11_lo"
                    print "The f1_name is {}".format(f1_name)
                    f10_rds_ctrl[x] = utils.generate_uuid()
                    command_result = target_f10_storage_obj.create_controller(ctrlr_uuid=f10_rds_ctrl[x],
                                                                              transport="RDS",
                                                                              nqn="nqn" + str(x),
                                                                              port=ipcfg_port,
                                                                              remote_ip=fs_server_storage_obj[
                                                                                  fs_server_come_keys[index]][f1_name],
                                                                              command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"],
                                           "F1_0 : Creation of RDS controller to remote {} : {}".
                                           format(fs_server_come_keys[index], f1_name))
                    if f1_name == "f11_lo":
                        index += 1
                        f1_index = False

                    # Attach volumes to RDS controller, 2 per controller
                    if num_servers == 1:
                        attach_cnt = 1
                    else:
                        attach_cnt = 2
                    for y in range(0, attach_cnt):
                        print "BLT_CNT is {}".format(blt_cnt)
                        print "NSID is {}".format(nsid)
                        command_result = target_f10_storage_obj.attach_volume_to_controller(ctrlr_uuid=f10_rds_ctrl[x],
                                                                                            ns_id=nsid,
                                                                                            vol_uuid=f10_blt_uuid[blt_cnt],
                                                                                            command_duration=command_timeout)
                        fun_test.simple_assert(command_result["status"],
                                               "Attaching RDS controller to BLT {}".format(blt_cnt))
                        blt_cnt += 1
                        nsid += 1

            #######################################################
            #   Check how many Server F1's needs to configured    #
            #######################################################
            # TODO servers should be able to scale to more storage F1s.
            if num_servers == 1:
                num_server_f1s = 1
            else:
                num_server_f1s = num_servers / 2
            index = 0
            f1_index = None
            fs_server_come_keys = fs_server_storage_obj.keys()
            rds_vol_uuid = {}
            rds_vol_cnt = 1
            nsid = 1
            pcie_controller = {}
            attach_nsid = 0
            for x in range(0, num_server_f1s):
                if not f1_index:
                    f1_name = "f10_obj"
                    f1_index = True
                    pcie_controller[f1_name] = {}
                    hu_ids = [2, 1]
                else:
                    f1_name = "f11_obj"
                    pcie_controller[f1_name] = {}
                    hu_ids = [1, 3]
                fs_obj = fs_server_storage_obj[fs_server_come_keys[index]][f1_name]

                if num_servers == 1:
                    vol_cnt = 1
                else:
                    vol_cnt = 2
                for vol_count in range(0, vol_cnt):
                    rds_vol_uuid[rds_vol_cnt] = utils.generate_uuid()
                    rds_vol_name = str(fs_server_come_keys[index]) + "_" + f1_name
                    command_result = fs_obj.create_volume(type="VOL_TYPE_BLK_RDS",
                                                          capacity=blt_capacity,
                                                          block_size=blt_blk_size,
                                                          name=rds_vol_name,
                                                          uuid=rds_vol_uuid[rds_vol_cnt],
                                                          remote_nsid=nsid,
                                                          remote_ip=f10_storage_loop_ip,
                                                          port=ipcfg_port,
                                                          command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "Creating RDS_vol_{}".format(nsid))
                    nsid += 1

                for hu_id in hu_ids:
                    attach_nsid += 1
                    pcie_controller[f1_name][hu_id] = utils.generate_uuid()
                    command_result = fs_obj.create_controller(transport="PCI",
                                                              ctrlr_uuid=pcie_controller[f1_name][hu_id],
                                                              ctlid=0,
                                                              huid=hu_id,
                                                              fnid=2,
                                                              command_duration=command_timeout)
                    fun_test.simple_assert(command_result["status"], "Create PCIe controller")

                    command_result = fs_obj.attach_volume_to_controller(ctrlr_uuid=pcie_controller[f1_name][hu_id],
                                                                        ns_id=attach_nsid,
                                                                        vol_uuid=rds_vol_uuid[rds_vol_cnt],
                                                                        command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"], "Attach RDS_vol_{}".format(x))

                if f1_name == "f11_obj":
                    index += 1
                    f1_index = None

        ##################################
        #  Get Host list connected to FS #
        ##################################
        all_host_list = []
        for fs in fun_test.shared_variables["server_fs"]:
            fs_host_info = testbed_info['fs']['fs-fcp-scale'][fs]['hu_host_list']
            for host in fs_host_info:
                for key, value in host.items():
                    if value == "x16":
                        all_host_list.append(key)

        host_list = all_host_list[:fun_test.shared_variables["num_servers"]]

        hosts_dict = {}
        # Create linux_obj, get nvme device name
        for hosts in host_list:
            hosts_dict[hosts] = {}
            hosts_dict[hosts]["handle"] = Linux(host_ip=hosts, ssh_username="localadmin", ssh_password="Precious1*")
            hosts_dict[hosts]["handle"].install_package("nvme-cli")
            hosts_dict[hosts]["handle"].install_package("fio")
            hosts_dict[hosts]["handle"].install_package("libaio-dev")
            hosts_dict[hosts]["nvme_device"] = get_nvme_device(hosts_dict[hosts]["handle"])
            if not hosts_dict[hosts]["nvme_device"]:
                hosts_dict[hosts]["handle"].disconnect()
                fun_test.test_assert(False, "NVMe device not found on {}".format(hosts))
            hosts_dict[hosts]["cpu_list"] = get_numa(hosts_dict[hosts]["handle"])
            hosts_dict[hosts]["handle"].disconnect()

        # Run fio write test from all hosts
        if precondition:
            print host_list
            wait_time = len(host_list)
            thread_count = 1
            thread_id = {}
            fio_output = {}
            for hosts in hosts_dict:
                print "Running Pre-condition on {}".format(hosts)
                host_clone = hosts_dict[hosts]["handle"].clone()
                thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                        func=fio_parser,
                                                                        host_index=thread_count,
                                                                        arg1=host_clone,
                                                                        filename=hosts_dict[hosts]["nvme_device"],
                                                                        rw="write",
                                                                        name="precondition_" + str(hosts),
                                                                        cpus_allowed=hosts_dict[hosts]["cpu_list"],
                                                                        timeout=600,
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

        # Run read fio test from all hosts
        wait_time = len(host_list)
        thread_count = 1
        thread_id = {}
        fio_output = {}
        fio_test = ["read"]
        host_thread_map = {}
        for test in fio_test:
            for hosts in hosts_dict:
                print "Running {} test on {}".format(test, hosts)
                host_clone = hosts_dict[hosts]["handle"].clone()
                temp = hosts_dict[hosts]["handle"].command("hostname")
                host_name = temp.strip()
                host_thread_map[thread_count] = host_name
                thread_id[thread_count] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                        func=fio_parser,
                                                                        host_index=thread_count,
                                                                        arg1=host_clone,
                                                                        filename=hosts_dict[hosts]["nvme_device"],
                                                                        rw=test,
                                                                        name=test + "_" + str(hosts),
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
                    iops_sum += fio_output[x]["read"]["iops"]
                    bw_sum += fio_output[x]["read"]["bw"]
                except Exception as ex:
                    fun_test.critical(str(ex))
                    fun_test.log("FIO Command Output for volume {}:\n {}".format(x, fio_output[x]))
            for hosts in hosts_dict:
                hosts_dict[hosts]["handle"].disconnect()
            print "******************************************************"
            print "Collective {} test IOP's is {}".format(test, iops_sum)
            print "******************************************************"

            # Check which host is giving highest latency and use that to plot latency
            fio_latency = fun_test.shared_variables["fio"]
            max_lat = 0
            for thread, value in fio_latency.iteritems():
                if value["read"]["latency90"] > max_lat:
                    max_lat = value["read"]["latency90"]
                    host_thread = thread
                    print "The max is {}".format(max_lat)
                    print "The host is {}".format(host_thread_map[host_thread])

            print "The final max is {}".format(max_lat)
            print "The final host is {}".format(host_thread_map[host_thread])

        table_data_headers = ["Block_Size", "IOPs", "BW in Gbps"]
        table_data_cols = ["read_block_size", "total_read_iops", "total_read_bw"]

        read_block_size = self.fio_cmd_args["bs"]
        total_read_iops = iops_sum
        total_read_bw = bw_sum
        row_data_list = []
        table_data_rows = []

        for item in table_data_cols:
            row_data_list.append(eval(item))
        table_data_rows.append(row_data_list)

        value_dict = {
            "block_size": read_block_size,
            "iops": total_read_iops,
            "bw": total_read_bw}

        # add_to_data_base(value_dict)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}

        fun_test.add_table(panel_header="NVMe RDS FCP Perf",
                           table_name=self.summary,
                           table_data=table_data)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(GetSetupDetails())
    ts.run()
