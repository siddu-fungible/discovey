from redfish import *


class BasicCase(Platform):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(BasicCase, self).setup()

    def run(self):
        fan_speed = self.get_fan_speed()
        temperature = self.get_temperature()
        self.check_ssd_status(self.expected_ssds)
        self.check_nu_ports(self.expected_ports_up)
        self.validate_fans()
        self.validate_temperaure_sensors()
        fun_test.log("\nFan speed: {}\nTemperature : {}".format(fan_speed, temperature))

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(BasicCase())
    myscript.run()
