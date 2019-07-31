from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController

from lib.fun.fs import Fs
from scripts.storage.storage_helper import *
from lib.host.apc_pdu import ApcPdu
from time import sleep

'''
Sanity Script for BLT Volume via PCI
'''


class BLTVolumeSanityScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Setup COMe, launch DPC cli
        3. 
        """)

    def setup(self):


        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 6
            self.command_timeout = 5
            self.reboot_timeout = 300
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        if not hasattr(self, "no_of_powercycles"):
            self.no_of_powercycles= 100

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)
        fun_test.shared_variables['topology'] = topology_helper.expanded_topology
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        fs = topology.get_dut_instance(index=0)

        am = fun_test.get_asset_manager()
        test_bed_type = fun_test.get_job_environment_variable("test_bed_type")
        fun_test.log("Testbed-type: {}".format(test_bed_type))
        test_bed_spec = am.get_test_bed_spec(name=test_bed_type)
        fun_test.simple_assert(test_bed_spec, "Test-bed spec for {}".format(test_bed_spec))
        dut_name = test_bed_spec["dut_info"]["0"]["dut"]
        fs_spec = am.get_fs_by_name(dut_name)
        fun_test.simple_assert(fs_spec, "FS spec for {}".format(dut_name))
        apc_info = fs_spec.get("apc_info", None)  # Used for power-cycling the entire FS

        fun_test.simple_assert(expression=apc_info, context=None, message='apc info details are correctl fed')
        outlet_no = apc_info.pop("outlet_number")

        print ('host_ip {} username {} password {}'.format(apc_info['host_ip'], apc_info['username'], apc_info['password']))

        for pc_no in range(0, no_of_powercycles):
            fun_test.log("Iteation no: {} out of {}".format(pc_no + 1, no_of_powercycles))
            apc_pdu = ApcPdu(host_ip = str(apc_info['host_ip']), username = str(apc_info['username']), password = str(apc_info['password']))

            sleep (5)
            apc_outlet_off_msg = apc_pdu.outlet_off(outlet_no)
            fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
            sleep (5)
            apc_outlet_on_msg = apc_pdu.outlet_on(outlet_no)
            fun_test.log("APC PDU outlet on mesg {}".format(apc_outlet_on_msg))
            sleep (5)

            apc_outlet_status_msg = apc_pdu.outlet_status(outlet_no)

            outlet_status = re.search(r"^olStatus.*Outlet\s+{}\s+.*(ON|OFF)".format(str(outlet_no)),
                    apc_outlet_status_msg, re.IGNORECASE|re.DOTALL|re.MULTILINE);
            fun_test.simple_assert(expression=outlet_status.groups()[0] == 'On', context=None,
                                    message="Power did not come back after pdu port reboot")

            fun_test.log("Check if platform components are up")
            sleep(120)
            fun_test.log("Check for fpga if it is up")

            fun_test.test_assert(expression=fs.get_fpga().ensure_host_is_up(max_wait_time=120),
                             context=fs.context, message="FPGA reachable after APC power-cycle")
            fun_test.log("fpga is up")
            fun_test.log("Check if BMC is up")
            fun_test.test_assert(expression=fs.get_bmc().ensure_host_is_up(max_wait_time=120),
                             context=fs.context, message="BMC reachable after APC power-cycle")
            fun_test.log("BMC is up")
            fun_test.log("Check if COMe is up")
            fun_test.test_assert(expression=fs.get_come().ensure_host_is_up(max_wait_time=120),
                                                                        message="ComE reachable after APC power-cycle")
            fun_test.log("COMe is up")

            try:
                apc_pdu.disconnect()
            except:
                pass

        import pdb
        pdb.set_trace()


    def cleanup(self):
        pass
        try:
            if fun_test.shared_variables['setup_created']:
                ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                blt_uuid = fun_test.shared_variables["blt_uuid"]
                # disconnect device from controller
                fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=ctrlr_uuid,
                    ns_id=self.ns_id,
                    command_duration=self.command_timeout)['status'],
                                     message="Detach nsid: {} from controller: {}".format(self.ns_id, ctrlr_uuid))

                # delete controller
                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(ctrlr_uuid))

                # delete BLT
                fun_test.test_assert(self.storage_controller.delete_volume(capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           type=self.blt_details["type"],
                                                                           name=self.blt_details["name"],
                                                                           uuid=blt_uuid,
                                                                           command_duration=self.command_timeout)
                                     ['status'],
                                     message="Delete Configured BLT")
        except Exception as ex:
            fun_test.critical(ex.message)
        finally:
            try:
                self.storage_controller.disconnect()
            except:
                pass
            try:
                fun_test.shared_variables["topology"].cleanup()
            except:
                pass


class BltPciSanityTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        pass
        mode = self.fio_mode
        end_host = fun_test.shared_variables["end_host"]
        nvme_block_device = fun_test.shared_variables['nvme_block_device']
        fio_numjob_iodepths = self.fio_numjobs_iodepth
        fun_test.simple_assert(nvme_block_device, "nvme block device available for test")
        for combo in fio_numjob_iodepths:
            num_jobs, iodepth = eval(combo)
            fio_job_name = "{}_{}_{}".format(self.fio_job_name, mode, iodepth * num_jobs)
            fio_output = end_host.pcie_fio(filename=nvme_block_device,
                                           rw=mode,
                                           numjobs=num_jobs,
                                           iodepth=iodepth,
                                           name=fio_job_name,
                                           **self.fio_cmd_args)
        fun_test.log("FIO Command Output:{}".format(fio_output))
        fun_test.test_assert(fio_output,
                             "Fio {} test for numjobs {} & iodepth {}".format(mode, num_jobs, iodepth))

    def cleanup(self):
        pass


class BltPciSeqRead(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test sequential read queries on BLT volume over nvme PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Seq Read test(without verify) from the end host.''')


class BltPciRandRead(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test random read queries on BLT volume over nvme PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Rand Read test(without verify) from the end host.''')


class BltPciSeqRWMix(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Sequential read-write mix 70:30 ratio queries on BLT volume over PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO mix seq read-write 70:30 test(without verify) from the end host.''')


class BltPciSeqWRMix(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test Sequential write-read mix 70:30 ratio queries on BLT volume over  PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO Seq write-read 70:30 test(without verify) from the end host.''')


class BltPciRandRWMix(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test Random read-write mix 70:30 ratio queries on BLT volume over PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO rand read-write 70:30 test(without verify) from the end host.''')


class BltPciRandWRMix(BltPciSanityTestcase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test Random read-write mix 70:30 ratio queries on BLT volume over PCI",
                              steps='''
        1. Create a BLT on FS attached with SSD.
        2. Export (Attach) this BLT to the external host connected via the PCI interface. 
        3. Pre-condition the volume with write test using fio.
        4. Run the FIO random write-read 70:30 test(without verify) from the end host.''')


if __name__ == "__main__":
    bltscript = BLTVolumeSanityScript()
    # bltscript.add_test_case(BltPciSeqRead())
    # bltscript.add_test_case(BltPciRandRead())
    # bltscript.add_test_case(BltPciSeqRWMix())
    # bltscript.add_test_case(BltPciSeqWRMix())
    bltscript.add_test_case(BltPciRandRWMix())
    # bltscript.add_test_case(BltPciRandWRMix())

    bltscript.run()
