from lib.system.fun_test import *
from scripts.system.platform_lib.platform_helper import *
from scripts.storage.pocs.apple.apc_pdu_auto import *


def run_decorator(func):
    def function_wrapper(self):
        self.run_passed = False
        func(self)
        self.run_passed = True
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
            if getattr(self, "work_around_power_cycle", False):
                apc_obj = RebootFs(self.fs)
                apc_obj.apc_pdu_reboot()
                Platform().fs_basic_checks()


class DiscoverStaticIp(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="discover communication static ip addresses (fs-142)",
                              test_rail_case_ids=["T23130"],
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_decorator
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


class DiscoverDhcpIp(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="discover communication dhcp ip with MAC reservation addresses (fs-143)",
                              test_rail_case_ids=["T23131"],
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_decorator
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


class AlternateCommunicationToBmc(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="alternate communication to platform via BMC",
                              test_rail_case_ids=["T23133"],
                              steps="""""")

    @run_decorator
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
        self.set_test_details(id=4,
                              summary="Verify Platform component versioning is according to release notes of DROP."
                                      "Revision should be detect correctly, with GPIO8_H for REV2 and GPIO8_L for REV1",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    @run_decorator
    def run(self):
        # todo: add revision  rev1 or rev2
        fpga_verified = self.verify_drop_version(system="fpga")
        fun_test.test_assert(fpga_verified, message="FPGA DROP version verified")
        bmc_verified = self.verify_drop_version(system="bmc")
        fun_test.test_assert(bmc_verified, message="BMC DROP version verified")
        come_verified = self.verify_drop_version(system="come")
        fun_test.test_assert(come_verified, message="COMe DROP version verified")


class BootSequenceFpga(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="boot sequence - FPGA Angstrom linux bootup",
                              steps="""
                              1. Get all the systems IP information
                              2. Reboot FPGA
                              3. Check if COMe and BMC are down
                              4. Check if the COMe and BMC boots back
                              5. Get all the systems IP information and verify with the old data(point 1.)""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceFpga, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_decorator
    def run(self):
        self.work_around_power_cycle = True
        self.fs_basic_checks()
        ip_data_before_reboot = self.get_mac_n_ip_addr_info_of_systems()
        fpga_reboot = self.reboot_system(system="fpga")
        fun_test.test_assert(fpga_reboot, "FPGA rebooted")
        bmc_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
                                                        time_in_seconds=5,
                                                        system="bmc",
                                                        time_out=30)
        come_down_thread = fun_test.execute_thread_after(func=self.check_if_system_is_down,
                                                         time_in_seconds=5,
                                                         system="come",
                                                         time_out=30)
        fpga_up = self.fpga_handle.ensure_host_is_up(max_wait_time=self.fpga_up_time_within)
        fun_test.test_assert(fpga_up, "FPGA up within {} seconds".format(self.fpga_up_time_within))

        fun_test.join_thread(bmc_down_thread)
        fun_test.join_thread(come_down_thread)
        #
        # self.fs_basic_checks()
        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()
        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def fs_basic_checks(self):
        Platform.fs_basic_checks(self)
        self.validate_fans()
        self.validate_temperaure_sensors()


class BootSequenceBmc(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="boot sequence - BMC bootup",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceBmc, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_decorator
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


class BootSequenceCome(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="boot sequence - COMe",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceCome, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_decorator
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


class BmcLinkToggle(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=8,
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
        super(BmcLinkToggle, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_decorator
    def run(self):
        bmc_up = self.bmc_handle.ensure_host_is_up()
        fun_test.test_assert(bmc_up, "BMC is up")

        max_time = 100
        timer = FunTimer(max_time=max_time)
        self.switch_to_bmc_console_for(for_time=max_time)

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


class BmcColdBoot(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        ApcPduTestcase.setup(self)
        self.initialize_test_case_variables(testcase)

    @run_decorator
    def run(self):
        ApcPduTestcase.run(self)

    def data_integrity_check(self):
        pass


class BmcIpmiReset(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        ApcPduTestcase.setup(self)
        self.initialize_test_case_variables(testcase)

    @run_decorator
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


class BmcTransportForCommunication(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="bmc transport for communication",
                              steps="""""")

    @run_decorator
    def run(self):
        bmc_up = self.bmc_handle.ensure_host_is_up()
        fun_test.test_assert(bmc_up, "BMC is reachable")
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")


class TemperatureSensorBmcIpmi(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="temperature sensor repository database of bmc",
                              steps="""""")

    @run_decorator
    def run(self):
        # todo:
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")
        result = self.verify_ipmi_sdr_info()


class FanSensorBootupIpmi(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=13,
                              summary="fan sensor repository database of bmc",
                              steps="""""")

    @run_decorator
    def run(self):
        response = self.check_ipmi_tool_connect()
        fun_test.test_assert(response, "IPMI tool is active")
        result = self.verify_ipmi_sdr_info(rpm_threshold=9000)


class TemperatureFanMeasurement(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=14,
                              summary="temperature and fan measurements reported on BMC(redfish)",
                              steps="""""")

    @run_decorator
    def run(self):
        self.validate_fans()
        self.validate_temperaure_sensors()


class InletExhasutThreshold(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=15,
                              summary="max/min threshold of sensor on BMC (inlet, exhaust)",
                              steps="""""")

    @run_decorator
    def run(self):
        # todo: verify i this is what we need to do
        self.validate_temperaure_sensors()


class FanRedfishtool(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=16,
                              summary="failure logs via ipmitool/redfish",
                              steps="""""")

    @run_decorator
    def run(self):
        #todo: not sure
        result = self.read_fans_data()
        self.validate_fans()


class F1AsicTemperature(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=17,
                              summary="F1 asic temperature",
                              steps="""""")

    @run_decorator
    def run(self):
        self.validate_temperaure_sensors()
        result = self.verify_ipmi_sdr_info()


class BootComeUefiOrBios(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=18,
                              summary="",
                              steps="""""")

    @run_decorator
    def run(self):
        # todo:
        # self.boot_come_uefi()
        self.check_if_f1s_detected()

        # self.boot_come_bios()
        self.check_if_f1s_detected()


class PcieDiscoverySsdViaRc(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=19,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(PcieDiscoverySsdViaRc, self).setup()
        self.initialize_test_case_variables(testcase)

    @run_decorator
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
        self.set_test_details(id=20,
                              summary="",
                              steps="""""")

    @run_decorator
    def run(self):
        self.check_if_f1s_detected()
        fun_test.log("Collecting 'lspci -vv -d1dad:' data")
        output = self.come_handle.command("lspci -vv -d1dad:")
        result = True if output else False
        fun_test.test_assert(result, "Collected lspci output")


class HostConnectionViaPcieBus(StorageApi, PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=21,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        testcase = self.__class__.__name__
        self.initialize_test_case_variables(testcase)

    @run_decorator
    def run(self):
        host_volume_map = {}
        host_volume_map[self.volume_creation_details["name"]] = "mktg-server-04"
        self.attach_volumes_to_host(host_volume_map)
        self.verify_nvme_connect()


class ComeVolumeCreation(PlatformGeneralTestCase, StorageApi):
    def describe(self):
        self.set_test_details(id=22,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        PlatformGeneralTestCase.setup(self)
        self.initialize_test_case_variables(testcase)
        StorageApi.__init__(self)

    @run_decorator
    def run(self):
        self.create_volume_and_run_fio()

    def cleanup(self):
        # PlatformGeneralTestCase.cleanup(self)
        pass


class SnakeTest(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=23,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        PlatformGeneralTestCase.setup(self)
        self.initialize_test_case_variables(testcase)

    @run_decorator
    def run(self):
        self.start_snake_test_verify(self.runtime)


class PortSplitTestCase(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=24,
                              summary="Port break down, regroup",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        PlatformGeneralTestCase.setup(self)
        # self.initialize_test_case_variables(testcase)
        self.load_new_image = True
        # self.initialize_dpcsh()

    @run_decorator
    def run(self):
        self.get_dpcsh_data_for_cmds("port enableall")
        self.docker_bringup_all_fpg_ports(f1=0)
        fun_test.sleep("Ports to be up", seconds=40)

        port_num = 0
        brkmode = "no_brk_100g"
        self.port_break_dpcsh(port_num, brkmode)

        port_num = 4
        self.port_break_dpcsh(port_num, brkmode)

        port_num = 0
        speed = "25g"
        self.split_n_verify_port_link_status(port_num, speed)

        port_num = 0
        brkmode = "no_brk_100g"
        self.port_break_dpcsh(port_num, brkmode)

        port_num = 4
        self.port_break_dpcsh(port_num, brkmode)

        self.verify_port_link_status_ethtool(f1=0, port_num_list=[1, 2, 3], speed="100g", link_detected="no")


class FanSpeedVariations(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=25,
                              summary="Fan speed variation check",
                              steps="""""")

    def setup(self):
        PlatformGeneralTestCase.setup(self)
        self.pwmtt = PwmTachtool(self.bmc_handle)

    @run_decorator
    def run(self):
        result = True
        fan = 0
        set_to_duty_cycle = 20
        sleep_for_sec = 300
        threshold_percentage = 20
        intial_rpm = 10000

        initial_speed = self.pwmtt.get_fan_speed(fan)
        normal_initial_speed = True if initial_speed < intial_rpm else False
        fun_test.test_assert(normal_initial_speed, "Initiall fan speed within {} RPM".format(intial_rpm))

        self.pwmtt.set_pwm_dutycycle(fan, set_to_duty_cycle)
        fun_test.test_assert(True, "Set Fan {} duty-cycle: {}".format(fan, set_to_duty_cycle))

        fan_speed_after_changing = self.pwmtt.get_fan_speed(fan)
        fun_test.sleep("For auto adjustment of fan", seconds=sleep_for_sec)
        fan_speed_after_waiting = self.pwmtt.get_fan_speed(fan)

        change_percentage = self.get_change(fan_speed_after_waiting, initial_speed)
        fun_test.log("Percentage change in the fan speed : {}".format(change_percentage))
        if change_percentage > threshold_percentage or change_percentage < 0:
            result = False
        fun_test.test_assert(result, "Fan speed normalized")

    @staticmethod
    def get_change(current, previous):
        if current == previous:
            return 0
        try:
            return (float(current - previous) / previous) * 100.0
        except ZeroDivisionError:
            return 0






class General(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=24,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    @run_decorator
    def run(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    test_case_list = [
        DiscoverStaticIp,
        DiscoverDhcpIp,
        AlternateCommunicationToBmc,
        PlatformComponentVersioningDiscovery,
        BootSequenceFpga,
        BootSequenceBmc,
        BootSequenceCome,
        BmcLinkToggle,
        BmcColdBoot,
        BmcIpmiReset,
        BmcTransportForCommunication,
        TemperatureSensorBmcIpmi,
        FanSensorBootupIpmi,
        TemperatureFanMeasurement,
        InletExhasutThreshold,
        FanRedfishtool,
        F1AsicTemperature,
        BootComeUefiOrBios,
        PcieDiscoverySsdViaRc,
        PcieDeviceDetection,
        HostConnectionViaPcieBus,
        ComeVolumeCreation,
        SnakeTest,
        PortSplitTestCase,
        FanSpeedVariations
        ]
    for i in test_case_list:
        myscript.add_test_case(i())
    myscript.run()
