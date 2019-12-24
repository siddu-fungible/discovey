from redfish import *
from scripts.storage.pocs.apple.apc_pdu_auto import *

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class DiscoverIPs(Platform):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Discover all the ips if they are reachable",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    def run(self):
        fpga_up = self.fpga_handle.is_host_up()
        fun_test.test_assert(fpga_up, "FPGA reachable")
        bmc_up = self.bmc_handle.is_host_up()
        fun_test.test_assert(bmc_up, "BMC reachable")
        come_up = self.fpga_handle.is_host_up()
        fun_test.test_assert(come_up, "COMe reachable")

    def cleanup(self):
        pass


class AlternateCommunicationToBMC(Platform):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Verifiy various communication to BMC",
                              steps="""""")

    def setup(self):
        super(AlternateCommunicationToBMC, self).setup()

    def run(self):
        # todo: ipmi tool;web interface;check with khallel
        redfish_active = self.check_if_redfish_is_active()
        fun_test.test_assert(redfish_active, "Redfishtool is active")
        bmc_serial = self.check_bmc_serial_console()
        fun_test.test_assert(bmc_serial, "BMC serial is active")

    def cleanup(self):
        pass


class PlatformComponentVersioningDiscovery(Platform):

    def describe(self):
        self.set_test_details(id=29,
                              summary="Verify Platform component versioning is according to release notes of DROP."
                                      "Revision should be detect correctly, with GPIO8_H for REV2 and GPIO8_L for REV1",
                              steps="""""")

    def setup(self):
        self.initialize_variables()
        self.intialize_handles()

    def run(self):
        fpga_verified = self.verify_drop_version(system="fpga")
        fun_test.test_assert(fpga_verified, message="FPGA DROP version verified")
        bmc_verified = self.verify_drop_version(system="bmc")
        fun_test.test_assert(bmc_verified, message="BMC DROP version verified")
        come_verified = self.verify_drop_version(system="come")
        fun_test.test_assert(come_verified, message="COMe DROP version verified")

    def cleanup(self):
        pass


class BootSequenceFPGA(Platform, ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=29,
                              summary="boot sequence-FPGA Angstrom linux bootup",
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

    def run(self):
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

        self.basic_checks()

        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()

        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def cleanup(self):
        pass


class BootSequenceBMC(Platform):

    def describe(self):
        self.set_test_details(id=30,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceBMC, self).setup()
        self.initialize_test_case_variables(testcase)

    def run(self):
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

        self.basic_checks()

        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()

        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def cleanup(self):
        pass


class BootSequenceCOMe(Platform):

    def describe(self):
        self.set_test_details(id=3,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(BootSequenceBMC, self).setup()
        self.initialize_test_case_variables(testcase)

    def run(self):
        ip_data_before_reboot = self.get_mac_n_ip_addr_info_of_systems()
        come_reboot = self.reboot_system(system="come")
        fun_test.test_assert(come_reboot, "COMe rebooted")

        come_down = self.check_if_system_is_down(system="come", time_out=30)
        fun_test.test_assert(come_down, "COMe Down")

        self.basic_checks()

        ip_data_after_reboot = self.get_mac_n_ip_addr_info_of_systems()
        self.compare_two_dict(ip_data_before_reboot, ip_data_after_reboot)

    def cleanup(self):
        pass


class BMCLinkToggle(Platform):

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

        bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=self.bmc_up_time_within)
        fun_test.test_assert(bmc_up, "BMC is up")

        if not timer.is_expired:
            fun_test.sleep("Waiting for BMC console to close", timer.remaining_time)

    def cleanup(self):
        pass


class BMCColdBoot(Platform):

    def describe(self):
        self.set_test_details(id=68,
                              summary="",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        ApcPduTestcase.setup(self)
        self.initialize_test_case_variables(testcase)

    def run(self):
        ApcPduTestcase.run(self)

    def data_integrity_check(self):
        pass

    def cleanup(self):
        pass


class BMCIPMIReset(BMCColdBoot):

    def describe(self):
        self.set_test_details(id=69,
                              summary="",
                              steps="""""")

    def setup(self):
        BMCColdBoot.setup(self)

    def run(self):
        self.ipmi_reset = True
        self.bmc_reboot = False
        BMCColdBoot.run(self)
        self.ipmi_reset = False
        self.bmc_reboot = True
        testcase = self.__class__.__name__
        self.initialize_test_case_variables(testcase)
        BMCColdBoot.run(self)

    def reboot_test(self):
        if self.ipmi_reset:
            self.ipmi_mgmt_reset()
        elif self.bmc_reboot:
            self.reboot_system(system="bmc")

    def ipmi_mgmt_reset(self):
        # todo: learn the command for this
        pass

    def cleanup(self):
        pass


class BMCTransportForCommunication(Platform):

    def describe(self):
        self.set_test_details(id=70,
                              summary="",
                              steps="""""")

    def setup(self):
        Platform.setup(self)

    def run(self):
        bmc_up = self.bmc_handle.ensure_host_is_up()
        fun_test.test_assert(bmc_up, "BMC is reachable")
        response = self.check_ipmitoll()
        fun_test.test_assert(response, "IPMI tool is active")

    def cleanup(self):
        pass


class TemperatureSensorBMCIpmi(Platform):

    def describe(self):
        self.set_test_details(id=71,
                              summary="",
                              steps="""""")

    def setup(self):
        Platform.setup(self)

    def run(self):
        # todo:
        self.connect_to_ipmi()
        self.get_sensor_sdr()
        self.verify_things()

    def cleanup(self):
        pass


class FanSensorIpmi(Platform):

    def describe(self):
        self.set_test_details(id=72,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


class TemperatureFanMeasurement(Platform):

    def describe(self):
        self.set_test_details(id=73,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


class TemperatureSensorDPU(Platform):

    def describe(self):
        self.set_test_details(id=74,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


class FanRedfishtool(Platform):

    def describe(self):
        self.set_test_details(id=78,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


class F1AsicTemperature(Platform):

    def describe(self):
        self.set_test_details(id=79,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


class General(Platform):

    def describe(self):
        self.set_test_details(id=3,
                              summary="",
                              steps="""""")

    def setup(self):
        pass

    def run(self):
        pass

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    # myscript.add_test_case(General())
    # myscript.add_test_case(DiscoverIPs())
    # myscript.add_test_case(AlternateCommunicationToBMC())
    # myscript.add_test_case(PlatformComponentVersioningDiscovery())
    # myscript.add_test_case(BootSequenceFPGA())
    # myscript.add_test_case(BootSequenceBMC())
    # myscript.add_test_case(BootSequenceCOMe())
    # myscript.add_test_case(BMCLinkToggle())
    # myscript.add_test_case(BMCColdBoot())
    # myscript.add_test_case(BMCColdBoot())
    # myscript.add_test_case(BMCTransportForCommunication())
    # myscript.add_test_case(TemperatureSensorBMCIpmi())
    myscript.add_test_case(FanSensorIpmi())
    myscript.run()