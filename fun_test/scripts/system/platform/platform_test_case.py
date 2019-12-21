from redfish import *
import telnetlib



class BasicCase(Platform):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(BasicCase, self).setup()
        t = telnetlib.Telnet()

    def run(self):
        self.get_platform_drop_information()

        self.set_platform_ip_information()
        self.get_platform_ip_information()

        self.set_platform_link()
        self.get_platform_link()

        self.get_platform_version_information()

        self.get_ssd_info()
        self.get_port_link_status()
        self.read_fans_data()
        self.read_dpu_data()
        self.reboot()
        self.power_on()
        self.power_off()
        self.connect_get_set_get_jtag()
        self.connect_get_set_get_i2c()

        fan_speed = self.read_fans_data()
        temperature = self.get_temperature()
        self.check_ssd_status(self.expected_ssds)
        self.check_nu_ports(self.expected_ports_up)
        self.validate_fans()
        self.validate_temperaure_sensors()
        fun_test.log("\nFan speed: {}\nTemperature : {}".format(fan_speed, temperature))


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(BasicCase())
    myscript.run()
