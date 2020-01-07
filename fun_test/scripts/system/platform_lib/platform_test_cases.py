from lib.system.fun_test import *
from scripts.system.platform_lib.platform_helper import *
from scripts.storage.pocs.apple.apc_pdu_auto import *


def run_deco(func):
    def function_wrapper(self):
        self.run_passed = True
        try:
            func(self)
        except Exception as ex:
            fun_test.critical(ex)
            self.run_passed = False
    return function_wrapper


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class PlatformGeneralTestCase(FunTestCase, Platform):
    def describe(self):
        self.set_test_details(id=1000,
                              summary="General Test case",
                              steps="""""")

    def setup(self):
        Platform.__init__(self)

    def run(self):
        pass

    def cleanup(self):
        if not getattr(self, "run_passed", False):
            self.collect_logs()


class DiscoverStaticIP(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="discover communication static ip addresses (fs-142)",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_deco
    def run(self):
        fpga_up = self.fpga_handle.is_host_up()
        fun_test.test_assert(fpga_up, "FPGA reachable")
        bmc_up = self.bmc_handle.is_host_up()
        fun_test.test_assert(bmc_up, "BMC reachable")
        come_up = self.come_handle.is_host_up()
        fun_test.test_assert(come_up, "COMe reachable")

    def initialize_variables(self):
        fs_name = "fs-142"
        self.fs = AssetManager().get_fs_spec(fs_name)


class DiscoverDhcpIP(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="discover communication dhcp ip with MAC reservation addresses (fs-143)",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_deco
    def run(self):
        fpga_up = self.fpga_handle.is_host_up()
        fun_test.test_assert(fpga_up, "FPGA reachable")
        bmc_up = self.bmc_handle.is_host_up()
        fun_test.test_assert(bmc_up, "BMC reachable")
        come_up = self.come_handle.is_host_up()
        fun_test.test_assert(come_up, "COMe reachable")

    def initialize_variables(self):
        fs_name = "fs-143"
        self.fs = AssetManager().get_fs_spec(fs_name)


class AlternateCommunicationToBMC(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="alternate communication to platform via BMC",
                              steps="""""")

    @run_deco
    def run(self):
        # todo: web interface check;
        redfish_active = self.check_if_redfish_is_active()
        fun_test.test_assert(redfish_active, "Redfishtool is active")
        bmc_serial = self.check_bmc_serial_console()
        fun_test.test_assert(bmc_serial, "BMC serial is active")
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")


class PlatformComponentVersioningDiscovery(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Verify Platform component versioning is according to release notes of DROP."
                                      "Revision should be detect correctly, with GPIO8_H for REV2 and GPIO8_L for REV1",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_deco
    def run(self):
        # todo: add revision  rev1 or rev2
        fpga_verified = self.verify_drop_version(system="fpga")
        fun_test.test_assert(fpga_verified, message="FPGA DROP version verified")
        bmc_verified = self.verify_drop_version(system="bmc")
        fun_test.test_assert(bmc_verified, message="BMC DROP version verified")
        come_verified = self.verify_drop_version(system="come")
        fun_test.test_assert(come_verified, message="COMe DROP version verified")


class BootSequenceFPGA(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=29,
                              summary="boot sequence - FPGA Angstrom linux bootup",
                              steps="""
                              1. Get all the systems IP information
                              2. Reboot FPGA
                              3. Check if COMe and BMC are down
                              4. Check if the COMe and BMC boots back
                              5. Get all the systems IP information and verify with the old data(point 1.)""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceFPGA, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        # self.fs_basic_checks()
        ip_data_before_reboot = self.get_mac_n_ip_addr_info_of_systems()
        # fpga_reboot = self.reboot_system(system="fpga")
        # fun_test.test_assert(fpga_reboot, "FPGA rebooted")
        # bmc_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
        #                                                 time_in_seconds=5,
        #                                                 system="bmc",
        #                                                 time_out=30)
        # come_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
        #                                                  time_in_seconds=5,
        #                                                  system="come",
        #                                                  time_out=30)
        # fpga_up = self.fpga_handle.ensure_host_is_up(max_wait_time=self.fpga_up_time_within)
        # fun_test.test_assert(fpga_up, "FPGA up within {} seconds".format(self.fpga_up_time_within))
        #
        # fun_test.join_thread(bmc_down_thread)
        # fun_test.join_thread(come_down_thread)
        #
        # self.fs_basic_checks()
        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()
        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def fs_basic_checks(self):
        Platform.fs_basic_checks(self)
        self.validate_fans()
        self.validate_temperaure_sensors()


class BootSequenceBMC(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=30,
                              summary="boot sequence - BMC bootup",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceBMC, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        self.fs_basic_checks()

        ip_data_before_reboot = self.get_mac_n_ip_addr_info_of_systems()
        bmc_reboot = self.reboot_system(system="bmc")
        fun_test.test_assert(bmc_reboot, "BMC rebooted")

        fpga_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
                                                         time_in_seconds=5,
                                                         system="fpga",
                                                         time_out=30)
        come_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
                                                         time_in_seconds=5,
                                                         system="come",
                                                         time_out=30)
        bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=self.bmc_up_time_within)
        fun_test.test_assert(bmc_up, "BMC up within {} seconds".format(self.bmc_up_time_within))
        fun_test.join_thread(fpga_down_thread)
        fun_test.join_thread(come_down_thread)

        self.fs_basic_checks()

        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()

        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def fs_basic_checks(self):
        ApcPduTestcase.basic_checks(self)
        self.validate_fans()
        self.validate_temperaure_sensors()


class BootSequenceCOMe(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=31,
                              summary="boot sequence - COMe",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceCOMe, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        self.fs_basic_checks()

        ip_data_before_reboot = self.get_mac_n_ip_addr_info_of_systems()

        if self.check_docker:
            self.come_handle.sudo_command("/opt/fungible/cclinux/cclinux_service.sh --stop", timeout=300)
        come_reboot = self.reboot_system(system="come")
        fun_test.test_assert(come_reboot, "COMe rebooted")

        self.check_if_system_is_down(system="come", time_out=30)

        come_up = self.come_handle.ensure_host_is_up(max_wait_time=self.come_up_time_within)
        fun_test.test_assert(come_up, "COMe up within {} seconds".format(self.come_up_time_within))

        self.fs_basic_checks()

        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()
        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def fs_basic_checks(self):
        ApcPduTestcase.basic_checks(self)
        self.validate_fans()
        self.validate_temperaure_sensors()


class BMCLinkToggle(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=64,
                              summary="""1. perform a physical/ifconfig up-down link toggle on BMC.
                                         2. observe failover of link on occasion of disconnect.""",
                              steps="""
                              1. Check if BMC is reachable
                              2. Check using ethtoll if bond0 is up
                              3. toggle it down
                              4. Verify BMC is not reachable, ethtool, ping
                              5. Turn the link up
                              6. Verify if the BMC is reachable now""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BMCLinkToggle, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        bmc_up = self.bmc_handle.ensure_host_is_up()
        fun_test.test_assert(bmc_up, "BMC is up")

        max_time = 100
        timer = FunTimer(max_time=max_time)
        self.switch_to_bmc_console(max_time=max_time)

        response = self.get_platform_link(system="bmc")
        fun_test.test_assert(response["link_detected"], "BMC bond0 interface is up (ethtool)")

        response = self.set_platform_link(system="bmc", action="down")
        fun_test.test_assert(response["status"], "Set BMC bond0 interface down")

        response = self.get_platform_link(system="bmc")
        fun_test.test_assert(not response["link_detected"], "BMC bond0 interface is down (ethtool)")

        bmc_down = self.bmc_handle.ensure_host_is_down()
        fun_test.test_assert(bmc_down, "BMC is not reachable")

        response = self.set_platform_link(system="bmc", action="up")
        fun_test.test_assert(response["status"], "Set BMC bond0 interface up")

        response = self.get_platform_link(system="bmc")
        fun_test.test_assert(response["link_detected"], "BMC bond0 interface is up (ethtool)")

        self.intialize_bmc_handle()

        bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=self.bmc_up_time_within)
        fun_test.test_assert(bmc_up, "BMC is up")

        if not timer.is_expired:
            fun_test.sleep("Waiting for BMC console to close", timer.remaining_time)


class BMCColdBoot(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=68,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        ApcPduTestcase.setup(self)
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        ApcPduTestcase.run(self)

    def data_integrity_check(self):
        pass


class BMCIPMIReset(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=69,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        ApcPduTestcase.setup(self)
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        self.warm_reboot = True
        self.cold_reboot = False
        ApcPduTestcase.run(self)
        self.warm_reboot = False
        self.cold_reboot = True
        self.iterations = 0
        ApcPduTestcase.run(self)

    def reboot_test(self):
        if self.warm_reboot:
            self.ipmitool_reset("warm")
        elif self.cold_reboot:
            self.ipmitool_reset("soft")


class BMCTransportForCommunication(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=70,
                              summary="bmc transport for communication",
                              steps="""""")

    @run_deco
    def run(self):
        bmc_up = self.bmc_handle.ensure_host_is_up()
        fun_test.test_assert(bmc_up, "BMC is reachable")
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")


class TemperatureSensorBMCIpmi(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=71,
                              summary="temperature sensor repository database of bmc",
                              steps="""""")

    @run_deco
    def run(self):
        # todo:
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")
        result = self.verify_ipmi_sdr_info()


class FanSensorBootupIpmi(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=72,
                              summary="fan sensor repository database of bmc",
                              steps="""""")

    @run_deco
    def run(self):
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")
        result = self.verify_ipmi_sdr_info(rpm_threshold=9000)


class TemperatureFanMeasurement(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=73,
                              summary="temperature and fan measurements reported on BMC(redfish)",
                              steps="""""")

    @run_deco
    def run(self):
        self.validate_fans()
        self.validate_temperaure_sensors()


class InletExhasutThreshold(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=74,
                              summary="max/min threshold of sensor on BMC (inlet, exhaust)",
                              steps="""""")

    @run_deco
    def run(self):
        # todo: verify i this is what we need to do
        self.validate_temperaure_sensors()


class FanRedfishtool(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=78,
                              summary="failure logs via ipmitool/redfish",
                              steps="""""")

    @run_deco
    def run(self):
        #todo: not sure
        result = self.read_fans_data()
        self.validate_fans()


class F1AsicTemperature(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=79,
                              summary="F1 asic temperature",
                              steps="""""")

    @run_deco
    def run(self):
        self.validate_temperaure_sensors()
        result = self.verify_ipmi_sdr_info()


class BootComeUEFIorBIOS(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=87,
                              summary="",
                              steps="""""")

    @run_deco
    def run(self):
        # todo:
        # self.boot_come_uefi()
        self.check_if_f1s_detected()

        # self.boot_come_bios()
        self.check_if_f1s_detected()


class PCIEDiscoverySSDviaRC(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=108,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(PCIEDiscoverySSDviaRC, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        fun_test.add_checkpoint("SSD check via DPCSH")
        # todo: check the dpch problem, and bmc method
        self.check_ssd_via_dpcsh()
        fun_test.add_checkpoint("SSD check via FPGA")
        self.check_ssd_via_fpga()
        fun_test.add_checkpoint("SSD check via BMC")
        # self.chech_ssd_via_bmc()


class PcieDeviceDetection(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=115,
                              summary="",
                              steps="""""")

    @run_deco
    def run(self):
        self.check_if_f1s_detected()
        fun_test.log("Collecting 'lspci -vv -d1dad:' data")
        output = self.come_handle.command("lspci -vv -d1dad:")
        result = True if output else False
        fun_test.test_assert(result, "Collected lspci output")


class HostConnectionViaPCIEBus(StorageAPI, PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=118,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        testcase = self.__class__.__name__
        self.initialize_test_case_variables(testcase)

    @run_deco
    def run(self):
        host_volume_map = {}
        host_volume_map[self.volume_creation_details["name"]] = "mktg-server-04"
        self.attach_volumes_to_host(host_volume_map)
        self.verify_nvme_connect()


class COMeVolumeCreation(PlatformGeneralTestCase, StorageAPI):
    def describe(self):
        self.set_test_details(id=3,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        PlatformGeneralTestCase.setup(self)
        self.initialize_test_case_variables(testcase)
        StorageAPI.__init__(self)

    @run_deco
    def run(self):
        self.create_volume_and_run_fio()

    # @run_deco
    # def run(self):
    #     storage_controller_0 = StorageController(target_ip=self.come_handle.host_ip,
    #                                              target_port=self.come_handle.get_dpc_port(0))
    #     ctrlr_uuid = utils.generate_uuid()
    #     fun_test.test_assert(storage_controller_0.create_controller(ctrlr_uuid=ctrlr_uuid,
    #                                                                 transport=transport,
    #                                                                 huid=huid[index],
    #                                                                 ctlid=ctlid[index],
    #                                                                 fnid=fnid,
    #                                                                 command_duration=120)['status'],
    #                          message="Create Controller with UUID: {}".format(ctrlr_uuid))

    def cleanup(self):
        # PlatformGeneralTestCase.cleanup(self)
        pass


class General(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    @run_deco
    def run(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    test_case_list = [
        DiscoverStaticIP,
        DiscoverDhcpIP,
        # AlternateCommunicationToBMC,
        # PlatformComponentVersioningDiscovery,
        # BootSequenceFPGA,
        # BootSequenceBMC,
        # BootSequenceCOMe,
        # BMCLinkToggle,
        # BMCColdBoot,
        # BMCIPMIReset,
        # BMCTransportForCommunication,
        # TemperatureSensorBMCIpmi,
        # FanSensorBootupIpmi,
        # TemperatureFanMeasurement,
        # InletExhasutThreshold,
        # FanRedfishtool,
        # F1AsicTemperature,
        # BootComeUEFIorBIOS,
        # PCIEDiscoverySSDviaRC,
        # PcieDeviceDetection,
        # HostConnectionViaPCIEBus,
        # COMeVolumeCreation
        ]
    for i in test_case_list:
        myscript.add_test_case(i())
    myscript.run()
