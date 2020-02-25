from lib.system.fun_test import *
from scripts.system.platform_lib.platform_test_cases import PlatformGeneralTestCase, PlatformScriptSetup, run_decorator


class TopLevelChassisInformation(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Top level chassis information",
                              test_rail_case_ids=["T31257"],
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
        validate = {"PowerState": "On", "Status": {'HealthRollup': 'OK', 'State': 'Enabled', 'Health': 'OK'},
                    "ChassisType": "StandAlone", "SKU": "somekey"}
        validated = self.dictionary_partially_equal(validate, chassis_data)
        fun_test.test_assert(validated, "Validated the chassis information")


class ChassisThermalMonitoringAndControl(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Chassis thermal monitoring and control",
                              test_rail_case_ids=["T31257"],
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
                              test_rail_case_ids=["T31259"],
                              steps="""""")

    @run_decorator
    def run(self):
        result = self.check_all_the_sensor_present()
        fun_test.test_assert(result, "Validated the chassis thermal information")
        self.validate_temperaure_sensors()

    def check_all_the_sensor_present(self):
        all_sensors_present = False
        expected_sensor_list = ["Inlet1", "Inlet2", "Exhaust1", "Exhaust2", "F1_0", "F1_1", "COMe", "FPGA"]
        response = self.chassis_thermal()
        if response["status"]:
            temperature_sensors = response["data"]["Temperatures"]
            sensors_list = [i["Name"] for i in temperature_sensors]
            all_sensors_present = all([i in sensors_list for i in expected_sensor_list])
        return all_sensors_present


class ArrayOfFanSensors(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Array of fan sensors",
                              test_rail_case_ids=["T31260"],
                              steps="""""")

    @run_decorator
    def run(self):
        result = self.check_fan_fields()
        fun_test.test_assert(result, "Validated fan fields")
        self.validate_fans()

    def check_fan_fields(self):
        result = True
        response = self.chassis_thermal()
        if response["status"]:
            fans = response["data"]["Fans"]
            validate = ["MemberId", "LowerThresholdCritical", "Reading", "PhysicalContext", "Name",
                        "LowerThresholdFatal", "ReadingUnits", "LowerThresholdNonCritical", "MaxReadingRange",
                        "MinReadingRange", "HotPluggable", "IndicatorLED", "Location", "Redundancy"]
            for each_fan in fans:
                validated = all([i in each_fan for i in validate])
                if not validated:
                    result = False
                    break
        return result


class ChassisPowerMonitoringAndControl(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Chassis power monitoring and control",
                              test_rail_case_ids=["T31261"],
                              steps="""""")

    @run_decorator
    def run(self):
        chassis_power = self.chassis_power()
        validate_values = self.check_power_metrics(chassis_power)
        fun_test.test_assert(validate_values, "Validate the power metrics values")

    def check_power_metrics(self, chassis_power):
        powermetrics = chassis_power["data"]["PowerControl"][0]["PowerMetrics"]
        validate_values = all([v != 0 for k, v in powermetrics.iteritems()])
        return validate_values


class AnArrayOfVoltageSensors(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="An array of voltage sensors.",
                              test_rail_case_ids=["T31262"],
                              steps="""""")

    @run_decorator
    def run(self):
        chassis_power = self.chassis_power()
        result = self.check_array_of_voltage_data(chassis_power)
        fun_test.test_assert(result, "Voltage info present in the power output")

    def check_array_of_voltage_data(self, chassis_power):
        if "Voltages" in chassis_power["data"]:
            result = True
        else:
            result = False
        return result


class ListOfManagementProcessorsInTheSystem(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=7,
                              summary="List of management processors in the system",
                              test_rail_case_ids=["T31263"],
                              steps="""""")

    @run_decorator
    def run(self):
        managers_output = self.managers()
        result = self.validate_manager_data(managers_output)
        fun_test.test_assert(result, "Validated managers output")

    def validate_manager_data(self, managers_output):
        if "ManagedBy" in managers_output["data"]:
            result = True
        else:
            result = False
        return result


class ServiceToInitiateSpecificAsynchronousTasks(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=8,
                              summary="Service to initiate and manage system specific asynchronous tasks",
                              test_rail_case_ids=["T31264"],
                              steps="""""")

    @run_decorator
    def run(self):
        result = False
        task = self.task_service()
        d = task["data"]["DateTime"]
        pyear = datetime.datetime.now().year
        pmonth = datetime.datetime.now().month
        fun_test.log("Year: {} Month: {}".format(pyear, pmonth))

        if int(d[0:4]) == pyear and int(d[5:7]) == pmonth:
            result = True
        fun_test.test_assert(result, "Datetime matching (taskservice output and sytem)")


class HttpsSessionsToTheRedfishService(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Service to establish and maintain HTTPS sessions to the Redfish service.",
                              test_rail_case_ids=["T31265"],
                              steps="""""")

    @run_decorator
    def run(self):
        sessions = self.sessions()
        result = self.check_for_active_session(sessions)
        fun_test.test_assert(result, "Validate sessions output")

    def check_for_active_session(self, sessions):
        if sessions["data"]["Members"]:
            result = True
        else:
            result = False
        return result


class ServiceToProvideUserAccountManagement(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Service to provide user account management",
                              test_rail_case_ids=["T31266"],
                              steps="""""")

    @run_decorator
    def run(self):
        account_service = self.account_service()
        result = self.validate_account_service(account_service)
        fun_test.test_assert(result, "Validate account service output")

    def validate_account_service(self, account_service):
        if "Authentication" in account_service["data"]:
            if "AuthenticationType" in account_service["data"]["Authentication"]:
                # Todo : add the varios authentications available
                result = True
        else:
            result = False
        return result


class ServiceToProvideEventNotificationToExternalConsumers(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Service to provide event notification to external consumers.",
                              test_rail_case_ids=["T31267"],
                              steps="""""")

    @run_decorator
    def run(self):
        event_service = self.event_service()
        result = self.validate_event_service(event_service)
        fun_test.test_assert(result, "Validate event service output")

    def validate_event_service(self, event_service):
        validate = ["DeliveryRetryAttempts", "DeliveryRetryIntervalSeconds", "Description", "EventTypesForSubscription",
                    "Name", "ServiceEnabled", "Status", "ResourceTypes", "SSEFilterPropertiesSupported"]
        validated = all([each_validate in event_service["data"] for each_validate in validate])
        return validated


class OemSpecificExtensionsToTheRedfishSchema(PlatformGeneralTestCase):

    def describe(self):
        self.set_test_details(id=12,
                              summary="OEM specific extensions to the Redfish schema.",
                              test_rail_case_ids=["T31268"],
                              steps="""""")

    @run_decorator
    def run(self):
        dynamic_extension = self.dynamic_extension()
        result = self.validate_event_service(dynamic_extension)
        fun_test.test_assert(result, "Validate dynamic extension output")

    def validate_event_service(self, event_service):
        validate = ["DeliveryRetryAttempts", "DeliveryRetryIntervalSeconds", "Description", "EventTypesForSubscription",
                    "Name", "ServiceEnabled", "Status", "ResourceTypes", "SSEFilterPropertiesSupported"]
        validated = all([each_validate in event_service["data"] for each_validate in validate])
        return validated


if __name__ == "__main__":
    platform = PlatformScriptSetup()
    test_case_list = [
        TopLevelChassisInformation,
        ChassisThermalMonitoringAndControl,
        ArrayOfTemperatureSensors,
        ArrayOfFanSensors,
        ChassisPowerMonitoringAndControl,
        AnArrayOfVoltageSensors,
        ListOfManagementProcessorsInTheSystem,
        ServiceToInitiateSpecificAsynchronousTasks,
        HttpsSessionsToTheRedfishService,
        ServiceToProvideUserAccountManagement,
        ServiceToProvideEventNotificationToExternalConsumers,
        OemSpecificExtensionsToTheRedfishSchema
    ]
    for i in test_case_list:
        platform.add_test_case(i())
    platform.run()