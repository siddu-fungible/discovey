from lib.system.fun_test import *
from scripts.system.platform_lib.platform_test_cases import PlatformGeneralTestCase, PlatformScriptSetup, run_decorator


class UART(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="UART2 should be accessible",
                              steps="""""")
    def run(self):
        self.bmc_handle.command("echo '' > /mnt/sdmmc0p1/log/sbp_0.log")
        self.bmc_handle.command("/mnt/sdmmc0p1/scripts/f1_reset.sh 0")
        fun_test.sleep("To reset F1s",seconds=20)
        uart_output=self.bmc_handle.command("cat /mnt/sdmmc0p1/log/sbp_0.log")
        self.validate_uart_info(uart_output)

    def validate_uart_info(self, uart_output):
        if "Boot success" in uart_output:
            result=True
        else:
            result=False
        fun_test.test_assert(result, "PASS")


if __name__ == "__main__":
    platform = PlatformScriptSetup()
    test_case_list = [UART]

    for i in test_case_list:
        platform.add_test_case(i())
    platform.run()


