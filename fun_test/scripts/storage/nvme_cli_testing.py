from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes

class NvmeCliTest():
    def __init__(self):

        pass

    def validate_id_ns(self):
        pass

    def clear_dmesg(self,host_handle):
        host_handle.sudo_command("dmesg -c")


    def get_dmesg(self,host_handle,string="Dmesg output"):
        pass

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


class RunNvmeIdentifyCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run all nvme identify commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run all nvme identify commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol2"
        already_deployed = False
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]

    def getCtrlId(self,lnx,device):
        op = json.loads(lnx.sudo_command("nvme -id-ctrl {DEVICE} -o=json".format(DEVICE=device)))
        print "Output : " + str(op)
        return op["cntlid"]

    def getNvmSetId(self,lnx,ns):
        op = json.loads(lnx.sudo_command("nvme -id-ns {NS} -o=json".format(NS=ns)))
        print "Output : " + str(op)
        return op["nvmsetid"]


    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device_ns = '/dev/' + nvme_device_name
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            identify_opcode = 06

            identify_cns_list = [0x00 , 0x01, 0x02, 0x03, 0x04, 0x05, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15,
                                 0x16, 0x17, 0x18, 0x19, 0x1F, 0x20, 0xFF]
            identify_cns_mandatory = [0x00, 0x01, 0x02, 0x03]
            cns_needing_nsid = [0x00, 0x02, 0x03, 0x10, 0x11, 0x12]
            cns_needing_cntid = [0x12, 0x13, 0x14, 0x15]
            test_result = True
            if 1:
                for cns in identify_cns_list:
                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if cns in cns_needing_nsid:
                        other_args += ' --namespace-id=' + str(nsid)

                    if cns in cns_needing_cntid:
                        # TBD
                        pass

                    command_result = host_handle.sudo_command("nvme admin-passthru {NVME_DEVICE} --opcode={IDENTIFY_OPCODE} --data-len=4096 "
                                          "--cdw10={CNS} {OTHER_ARGS} -r".format(NVME_DEVICE=nvme_device,
                                                                              IDENTIFY_OPCODE=identify_opcode, CNS=cns, OTHER_ARGS=other_args))
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for Identify CNS {CNS}".format(CNS=cns)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  Identify CNS {CNS}".format(CNS=cns))
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for Identify CNS {CNS}".format(CNS=cns),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)



                    # For mandatory commands, we should not get this error
                    if cns in identify_cns_mandatory:
                        result_temp = "ERR epnvme " not in relevant_logs
                        if not result_temp:
                            fun_test.critical("NVME command is NOT accepted Mandatory Identify CNS {CNS}".format(CNS=cns))

                        fun_test.add_checkpoint(checkpoint="Validate NVME command is accepted for Identify CNS {CNS}".format(CNS=cns),
                                                        expected=True, actual=result_temp)

                        test_result &= result_temp

                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for Identify CNS {CNS}".format(CNS=cns))
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for Identify CNS {CNS}".format(CNS=cns),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp

            identify_cmd_list = ['id-ns', 'id-ns-granularity', 'list-ns', 'id-ctrl', 'list-ctrl', 'id-nvmset', 'id-uuid']
            identify_cmd_variations = {
                'id-ns' : [None, ' -f '],
                'id-ns-granularity' : [None],
                'list-ns' : [' --all', ' --namespace-id={NSID}'.format(NSID=str(nsid)) ],
                'id-ctrl' : [None],
                'list-ctrl' : [' --cntid=' + str(self.getCtrlId(host_handle,nvme_device)), ' --namespace-id={NSID}'.format(NSID=str(nsid))],
                'id-nvmset' : [None, ' --nvmset=' + str(self.getNvmSetId(host_handle,nvme_device_ns)) ],
                'id-uuid' : [None]
            }

            for identify_cmd in identify_cmd_list:

                for variation in identify_cmd_variations[identify_cmd]:
                    variation_args = ''
                    if variation is None:
                        variation_args = ''
                    else:
                        variation_args += variation

                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if identify_cmd == "id-ns" :
                        other_args += ' --namespace-id=' + str(nsid)
                        other_args += ' -H'


                    if identify_cmd not in ["list-ns", "list-ctrl"]:
                        other_args += " --output-format=json"


                    nvme_cmd = "nvme {IDENTIFY_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                    IDENTIFY_CMD=identify_cmd,NVME_DEVICE=nvme_device,
                                            OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)
                    command_result = host_handle.sudo_command(nvme_cmd)
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for {NVME_CMD}".format(NVME_CMD=nvme_cmd)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)


                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp



            fun_test.test_assert(expression=test_result, message="Identify test result")

            #traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
            #                                                                    filename="/dev/"+nvme_device_name)
            #fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            #fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup()

class RunNvmeGetFeatureCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run all nvme Get Feature commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run all nvme Get Feature commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol"
        already_deployed = False
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]

    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            feature_id_list = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
                               0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x77, 0x78, 0x7F, 0x80, 0xBF, 0xC0, 0xFF,
                               0x81, 0x82, 0x83, 0x84, 0x85]

            feature_uses_buffer_mem = [0x03, 0x0C, 0x0E, 0x13, 0x16, 0x81]

            test_result = True
            for feature in feature_id_list:
                for sel in [-1,0,1,2,3]:
                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if feature in feature_uses_buffer_mem:
                        other_args += ' --data-len=4096'

                    if sel > -1:
                        other_args += ' --sel=' + str(sel)



                    command_result = host_handle.sudo_command("nvme get-feature {NVME_DEVICE}  --feature-id={FEATURE} -H {OTHER_ARGS}".format(NVME_DEVICE=nvme_device,
                                                                                                                FEATURE=feature, OTHER_ARGS=other_args))
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for Get Feature {FEATURE} Select value {SEL}".format(FEATURE=feature,SEL=sel)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  Identify CNS {CNS}")
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for Get Feature {FEATURE} Select value {SEL}".format(FEATURE=feature,SEL=sel),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)


                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for Identify CNS {CNS}")
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for Get Feature {FEATURE} Select value {SEL}".format(FEATURE=feature,SEL=sel),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp

                    #Validate the get feature values
                    #TBD

            fun_test.test_assert(expression=test_result, message="Identify test result")

            #traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
            #                                                                    filename="/dev/"+nvme_device_name)
            #fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            #fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup()


class RunNvmeGetLogCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run all nvme Get Log commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run all nvme Get Log commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol2"
        already_deployed = False
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]


    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device_ns = '/dev/' + nvme_device_name
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            log_identifier_list = [0x00 , 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E,
                                   0x0F, 0x10, 0x6F, 0x70, 0x71, 0x7F, 0x80, 0x81, 0xC0, 0xFF, 0x82, 0xBF]

            variations = [None, ' --lpo=50 --rae']

            test_result = True
            if 0:
                for log_id in log_identifier_list:
                    for variation in variations:
                        variation_args = ''
                        if variation is None:
                            variation_args = ''
                        else:
                            variation_args += variation

                        # Clear dmesg before start of test
                        host_handle.sudo_command("dmesg -c")
                        other_args = ''

                        other_args += ' --namespace-id=' + str(nsid)
                        other_args += ' --log-len=4096'

                        command_result = host_handle.sudo_command("nvme get-log {NVME_DEVICE} --log-id={LOG_ID} "
                                                                  "{OTHER_ARGS} {VARIATION_ARGS}".format(NVME_DEVICE=nvme_device,
                                                                                  LOG_ID=log_id, OTHER_ARGS=other_args, VARIATION_ARGS=variation_args))
                        print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                        time.sleep(5)
                        dmesg = host_handle.sudo_command("dmesg")
                        print "Dmesg for Get Log {LOG_ID}".format(LOG_ID=log_id)
                        print str(dmesg)

                        result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                        if not result_temp:
                            fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  Get Log {LOG_ID}".format(LOG_ID=log_id))
                        fun_test.add_checkpoint(checkpoint="Validate dmesg for Get Log {LOG_ID}".format(LOG_ID=log_id),
                                                expected=True, actual=result_temp)

                        test_result &= result_temp

                        # Read uart log file
                        relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                        print "Relevant logs " + str(relevant_logs)

                        last_line_in_log_file = relevant_logs.split("\n")[-1]
                        last_timestamp = last_line_in_log_file.split(' ')[0]
                        uart_last_timestamp = last_timestamp.replace("[", '')
                        print "Next Uart last time stamp is " + str(uart_last_timestamp)


                        # Connection should not be reset
                        result_temp = "Got close notification for queue " not in relevant_logs
                        if not result_temp:
                            fun_test.critical("Connection is reset for Get Log {LOG_ID}".format(LOG_ID=log_id))
                        fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for Get Log {LOG_ID}".format(LOG_ID=log_id),
                                                        expected=True, actual=result_temp)

                        test_result &= result_temp

            get_log_cmd_list = ['telemetry-log', 'fw-log', 'changed-ns-list-log', 'smart-log', 'ana-log', 'error-log',
                                'effects-log', 'endurance-log', 'self-test-log', 'sanitize-log']
            get_log_cmd_variations = {
                'telemetry-log' : [' --host-generate=1 --controller-init -o txt ',
                                   ' --host-generate=1 --controller-init --data-area=1 -o txt ',
                                   '  --data-area=2 -o txt',
                                   ' --host-generate=1 --controller-init --data-area=3 -o txt'],
                'fw-log' : [None],
                'changed-ns-list-log': [None],
                'smart-log' : [None, ' --namespace-id={NSID}'.format(NSID=str(nsid)) ],
                'ana-log' : [None],
                'error-log': [None, ' --log-entries=10'],
                'effects-log': [None],
                'endurance-log': [None],
                'self-test-log' : [None, ' --namespace-id={NSID}'.format(NSID=str(nsid))],
                'sanitize-log' : [None],

            }

            for get_log_cmd in get_log_cmd_list:

                for variation in get_log_cmd_variations[get_log_cmd]:
                    variation_args = ''
                    if variation is not None:
                        variation_args += variation

                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if get_log_cmd in ['fw-log', 'changed-ns-list-log', 'smart-log', 'ana-log', 'error-log', 'effects-log', 'endurance-log', 'self-test-log', 'sanitize-log']:
                        other_args += " --output-format=json"



                    nvme_cmd = "nvme {LOG_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                    LOG_CMD=get_log_cmd,NVME_DEVICE=nvme_device,
                                            OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)
                    command_result = host_handle.sudo_command(nvme_cmd)
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for {NVME_CMD}".format(NVME_CMD=nvme_cmd)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)


                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp


            fun_test.test_assert(expression=test_result, message="Get Log test result")

            #traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
            #                                                                    filename="/dev/"+nvme_device_name)
            #fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            #fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup()

class RunNvmeGetPropertyCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run all nvme Get Property commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run all nvme Get Property commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol"
        already_deployed = True
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]

    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            property_list = [0x0, 0x8, 0x14, 0x1c, 0x20, 0x30 ]


            test_result = True
            for property in property_list:
                # Clear dmesg before start of test
                host_handle.sudo_command("dmesg -c")
                other_args = ''

                command_result = host_handle.sudo_command("nvme get-property {NVME_DEVICE}  --offset={PROPERTY} -H {OTHER_ARGS}".format(NVME_DEVICE=nvme_device,
                                                                                                            PROPERTY=property, OTHER_ARGS=other_args))
                print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                time.sleep(5)
                dmesg = host_handle.sudo_command("dmesg")
                print "Dmesg for Get Property {PROPERTY} ".format(PROPERTY=property)
                print str(dmesg)

                result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                if not result_temp:
                    fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  Identify CNS {CNS}")
                fun_test.add_checkpoint(checkpoint="Validate dmesg for Get Property {PROPERTY} ".format(PROPERTY=property),
                                        expected=True, actual=result_temp)

                test_result &= result_temp

                # Read uart log file
                relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                print "Relevant logs " + str(relevant_logs)

                last_line_in_log_file = relevant_logs.split("\n")[-1]
                last_timestamp = last_line_in_log_file.split(' ')[0]
                uart_last_timestamp = last_timestamp.replace("[", '')
                print "Next Uart last time stamp is " + str(uart_last_timestamp)


                # Connection should not be reset
                result_temp = "Got close notification for queue " not in relevant_logs
                if not result_temp:
                    fun_test.critical("Connection is reset for Get Property {PROPERTY} ".format(PROPERTY=property))
                fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for Get Property {PROPERTY} ".format(PROPERTY=property),
                                                expected=True, actual=result_temp)

                test_result &= result_temp

                #Validate the get feature values
                #TBD

            fun_test.test_assert(expression=test_result, message="Get Property test result")

            #traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
            #                                                                    filename="/dev/"+nvme_device_name)
            #fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            #fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup()


class RunNvmeOtherCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run P2 NVME CLI commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run P2 NVME CLI commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol2"
        already_deployed = False
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]

    def getCtrlId(self,lnx,device):
        op = json.loads(lnx.sudo_command("nvme -id-ctrl {DEVICE} -o=json".format(DEVICE=device)))
        print "Output : " + str(op)
        return op["cntlid"]


    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device_ns = '/dev/' + nvme_device_name
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            test_result = True


            nvme_cmd_list = ['list-secondary', 'ns-descs', 'get-ns-id', 'ns-rescan', 'device-self-test', 'sanitize',
                             'show-regs', 'dir-receive', 'dir-send', 'get-lba-status', 'resv-acquire', 'resv-register',
                             'resv-release', 'resv-report']
            nvme_cmd_variations = {
                'list-secondary' : [None, ' --namespace-id={NSID} --num-entries=5'.format(NSID=str(nsid)), ' --cntid=' + str(self.getCtrlId(host_handle,nvme_device)) ],
                'ns-descs' : [None, ' --namespace-id={NSID} '.format(NSID=str(nsid)) ],
                'get-ns-id': [None],
                'ns-rescan' : [None],
                'device-self-test' : [None, ' --namespace-id={NSID} '.format(NSID=str(nsid)), ' --self-test-code=0x1',
                                      ' --namespace-id={NSID}  --self-test-code=0x2'.format(NSID=str(nsid)), ' --self-test-code=0xeh' , ' --self-test-code=0xfh'],
                'sanitize': [None, ' --no-dealloc --sanact=0', ' --sanact=1', ' --sanact=2', ' --oipbp --owpass=0 --sanact=3', ' --ause --sanact=4'],
                'show-regs': [None],
                'dir-receive': [' --dir-type 0 --dir-oper 1 --human-readable', ' --dir-type 1 --dir-oper 1 --human-readable',
                                ' --dir-type 1 --dir-oper 2 --human-readable', ' USE_NS --dir-type 1 --dir-oper 3 --req-resource 3 --human-readable'],
                'dir-send': [' USE_NS --dir-type 0 --dir-oper 1 --target-dir 1 --endir 1 ', ' USE_NS --dir-type 0 --dir-oper 1 --target-dir 1 --endir 0',
                             ' USE_NS --dir-type 1 --dir-oper 2', ' --dir-type 1 --dir-oper 1 --dir-spec 3'],
                'get-lba-status': [' USE_NS -start-lba=1023 -range-len=5 --action=0x10', ' USE_NS -start-lba=1023  --action=0x11'],
                'resv-acquire': [' USE_NS'],
                'resv-release': [' USE_NS'],
                'resv-register': [' USE_NS'],
                'resv-report': [' USE_NS'],


            }

            for nvme_option in nvme_cmd_list:

                for variation in nvme_cmd_variations[nvme_option]:
                    variation_args = ''
                    if variation is not None:
                        if 'USE_NS' in variation:
                            variation_args += variation.replace('USE_NS', nvme_device_ns)
                        else:
                            variation_args += variation

                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if nvme_option in ['list-secondary', 'ns-descs', 'show-regs']:
                        other_args += " --output-format=json"


                    if nvme_option in ["ns-descs", "get-ns-id"]:
                        nvme_cmd = "nvme {LOG_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                        LOG_CMD=nvme_option,NVME_DEVICE=nvme_device_ns,
                                                OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)

                    elif nvme_option in ['dir-receive', 'dir-send', 'get-lba-status', 'resv-acquire', 'resv-release', 'resv-register', 'resv-report']:
                        if 'USE_NS' in variation:
                            nvme_cmd = "nvme {LOG_CMD} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                            LOG_CMD=nvme_option,
                                                    OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)
                        else:
                            nvme_cmd = "nvme {LOG_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                LOG_CMD=nvme_option, NVME_DEVICE=nvme_device,
                                OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)

                    else:

                        nvme_cmd = "nvme {LOG_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                        LOG_CMD=nvme_option,NVME_DEVICE=nvme_device,
                                                OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)
                    command_result = host_handle.sudo_command(nvme_cmd)
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for {NVME_CMD}".format(NVME_CMD=nvme_cmd)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)


                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp


            fun_test.test_assert(expression=test_result, message="Get NVME other commands test result")

            #traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
            #                                                                    filename="/dev/"+nvme_device_name)
            #fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
            #fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup()

class RunNvmeIOCommands(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run NVME IO commands",
                              steps='''
                              1. Make sure API server is up and running
                              2. Run NVME IO commands
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        name = "blt_vol2"
        already_deployed = False
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 160027797094
        compression_effort = False
        encrypt = False
        body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                           compression_effort=compression_effort,
                                                           encrypt=encrypt, data_protection={})
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=already_deployed)

        fs_obj_list = []
        self.bond_interface_dict = {}
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            dut = self.topology.get_dut(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                bond_interface_ip = dut.get_bond_interfaces(f1_index=f1_index)[0]
                dataplane_ip = str(bond_interface_ip.ip).split('/')[0]
                self.bond_interface_dict[dataplane_ip] = f1_index
            fs_obj_list.append(fs_obj)

        print "Bond interface dict is " + str(self.bond_interface_dict)
        self.fs_obj = fs_obj_list[0]

        vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=fs_obj_list,
                                                                       body_volume_intent_create=body_volume_intent_create)
        fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
        hosts = self.topology.get_available_host_instances()
        for index, fs_obj in enumerate(fs_obj_list):
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[index],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            print "Attach volume result is " + str(attach_vol_result)

        self.f1_index = self.bond_interface_dict[str(attach_vol_result[0]["data"]["ip"])]

    def getCtrlId(self,lnx,device):
        op = json.loads(lnx.sudo_command("nvme -id-ctrl {DEVICE} -o=json".format(DEVICE=device)))
        print "Output : " + str(op)
        return op["cntlid"]


    def run(self):
        hosts = self.topology.get_available_hosts()
        bmc_handle = self.fs_obj.get_bmc()
        # Get uart log file
        uart_log_file = bmc_handle.get_f1_uart_log_file_name(self.f1_index)
        print "Uart log file is " + uart_log_file

        # Read uart log file
        log_file_contents = bmc_handle.command("tail -n 2 " + str(uart_log_file))
        #print "Log file contents " + str(log_file_contents)

        # Get last timestamp logged
        last_line_in_log_file = log_file_contents.split("\n")[-1]
        last_timestamp = last_line_in_log_file.split(' ')[0]
        uart_last_timestamp = last_timestamp.replace("[", '')
        print "Uart last time stamp is " + str(uart_last_timestamp)



        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
            nvme_device_ns = '/dev/' + nvme_device_name
            nvme_device = '/dev/' + nvme_device_name[0:-2]
            nsid = nvme_device_name[-1:]

            test_result = True

            # 'compare', 'read', 'write', 'verify',
            nvme_cmd_list = ['write-zeroes', 'format', 'flush', 'reset', 'subsystem-reset']
            nvme_cmd_variations = {
                'write-zeroes': [' USE_NS  --start-block=1023 --block-count=0', ' --start-block=1010 --block-count=10 --namespace-id={NSID} '.format(NSID=str(nsid)),
                                  ' USE_NS  --start-block=1023 --block-count=0 --deac --force-unit-access',
                                  ' USE_NS  --start-block=1023 --block-count=0 ',
                                  ],
                'format': [' USE_NS -f', ' --namespace-id={NSID} --ses=1 --pi=1 -r -f'.format(NSID=str(nsid)),],
                'flush': [None, ' USE_NS', ' --namespace-id={NSID}'.format(NSID=str(nsid)), ],
                'reset': [None],
                'subsystem-reset': [None],
            }

            for nvme_option in nvme_cmd_list:

                for variation in nvme_cmd_variations[nvme_option]:
                    variation_args = ''
                    if variation is not None:
                        variation_args += variation

                    # Clear dmesg before start of test
                    host_handle.sudo_command("dmesg -c")
                    other_args = ''
                    if nvme_option in ['list-secondary', 'ns-descs', 'show-regs']:
                        other_args += " --output-format=json"


                    if 'USE_NS' in variation_args:
                        dev = nvme_device_ns
                        variation_args.replace('USE_NS', '')
                    else:
                        dev = nvme_device

                    nvme_cmd = "nvme {LOG_CMD} {NVME_DEVICE} {OTHER_ARGS} {VARIATION_ARGS} ".format(
                                    LOG_CMD=nvme_option,NVME_DEVICE=dev,
                                            OTHER_ARGS=other_args, VARIATION_ARGS=variation_args)

                    command_result = host_handle.sudo_command(nvme_cmd)
                    print "Command result is {COMMAND_RESULT}".format(COMMAND_RESULT=command_result)

                    time.sleep(5)
                    dmesg = host_handle.sudo_command("dmesg")
                    print "Dmesg for {NVME_CMD}".format(NVME_CMD=nvme_cmd)
                    print str(dmesg)

                    result_temp = "failed to connect socket" not in dmesg or "Call Trace:" not in dmesg
                    if not result_temp:
                        fun_test.critical("failed to connect socket or Call Trace: found in dmesg for  for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate dmesg for for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                            expected=True, actual=result_temp)

                    test_result &= result_temp

                    # Read uart log file
                    relevant_logs = bmc_handle.command("grep -A 100 {FILTER} {LOG_FILE}".format(FILTER=uart_last_timestamp, LOG_FILE=str(uart_log_file)))
                    print "Relevant logs " + str(relevant_logs)

                    last_line_in_log_file = relevant_logs.split("\n")[-1]
                    last_timestamp = last_line_in_log_file.split(' ')[0]
                    uart_last_timestamp = last_timestamp.replace("[", '')
                    print "Next Uart last time stamp is " + str(uart_last_timestamp)


                    # Connection should not be reset
                    result_temp = "Got close notification for queue " not in relevant_logs
                    if not result_temp:
                        fun_test.critical("Connection is reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd))
                    fun_test.add_checkpoint(checkpoint="Validate whether connection is not reset for {NVME_CMD}".format(NVME_CMD=nvme_cmd),
                                                    expected=True, actual=result_temp)

                    test_result &= result_temp


            fun_test.test_assert(expression=test_result, message="Run NVME IO test result")


    def cleanup(self):
        self.storage_controller_template.cleanup()

if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RunNvmeIdentifyCommands())
    setup_bringup.add_test_case(RunNvmeGetFeatureCommands())
    setup_bringup.add_test_case(RunNvmeGetLogCommands())
    setup_bringup.add_test_case(RunNvmeGetPropertyCommands())
    setup_bringup.add_test_case(RunNvmeOtherCommands())
    setup_bringup.add_test_case(RunNvmeIOCommands())

    setup_bringup.run()
