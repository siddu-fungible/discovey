from lib.system.fun_test import *
from scripts.system.platform_lib.platform_test_cases import PlatformGeneralTestCase, PlatformScriptSetup, run_decorator


class TopLevelChassisInformation(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Top level chassis information",
                              steps="""""")

    def run(self):
        chassis_output = self.chassis()
        self.validate_chassis_information(chassis_output)

    def dictionary_partially_equal(self, partial_dict, dict_2):
        result = True
        for k, v in partial_dict.iteritems():
            if type(v) != dict:
                if v == dict_2[k]:
                    continue
                else:
                    return False
            elif type(v) == dict:
                result = self.dictionary_partially_equal(v, dict_2[k])
                if not result:
                    break
        return result

    def validate_chassis_information(self, chassis_output):
        chassis_data = chassis_output["data"]
        validate = {"PowerState": "On", "Status": {'HealthRollup': 'OK', 'State': 'Enabled', 'Health': 'OK'}}
        validated = self.dictionary_partially_equal(validate, chassis_data)
        fun_test.test_assert(validated, "Validated the chassis information")


class ChassisThermalMonitoringAndControl(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Chassis thermal monitoring and control",
                              steps="""""")

    @run_decorator
    def run(self):
        chassis_thermal = self.chassis_thermal()
        self.validate_thermal(chassis_thermal)

    def validate_thermal(self, chassis_thermal):
        thermal_data = chassis_thermal["data"]
        validate = ["Fans", "Temperatures"]
        validated = [i in thermal_data for i in validate]
        fun_test.test_assert(all(validated), "Validated the Chassis thermal fans and temperatures sensors data")


class ArrayOfTemperatureSensors(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Array of temperature sensors",
                              steps="""""")

    @run_decorator
    def run(self):
        self.validate_temperaure_sensors()
        # fun_test.test_assert(vlaidate_thermal, "Validated the chassis thermal information")


class ArrayOfFanSensors(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Array of fan sensors",
                              steps="""""")

    @run_decorator
    def run(self):
        self.validate_fans()


class ChassisPowerMonitoringAndControl(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Chassis power monitoring and control",
                              steps="""""")
    @run_decorator
    def run(self):
        task = self.task_service()

        chassis_power = self.chassis_power()
        aw = chassis_power['data']["PowerControl"][0]["PowerMetrics"]["AverageConsumedWatts"]
        if aw==0:
            result = False
        else:
            result = True
        fun_test.test_assert(result, "PASS")

class Taskserviceverify(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Service to initiate and manage system specific asynchronous tasks",
                              steps="""""")

    @run_decorator
    def run(self):
        result = False
        task = self.task_service()
        d = task["data"]["DateTime"]
        pyear=datetime.datetime.now().year
        pmonth=datetime.datetime.now().month
        fun_test.log(pyear)
        fun_test.log(pyear)

        if int(d[0:4]) == pyear and int(d[5:7]) == pmonth:
            result=True
        fun_test.test_assert(result, "datetime is matching")





if __name__ == "__main__":
    platform = PlatformScriptSetup()
    test_case_list = [
        #TopLevelChassisInformation,
        # ChassisThermalMonitoringAndControl,
        # ArrayOfTemperatureSensors,
        # ArrayOfFanSensors,
        # ChassisPowerMonitoringAndControl,
        Taskserviceverify
    ]
    for i in test_case_list:
        platform.add_test_case(i())
    platform.run()

