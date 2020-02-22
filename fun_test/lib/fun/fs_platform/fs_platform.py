from lib.system.fun_test import fun_test


class FsPlatform:
    #images_to_check = ['pufr', 'frmw', 'husc', 'husd', 'hbsb', 'husm', 'host', 'kbag', 'emmc']
    images_to_check = ['pufr', 'frmw', 'husc', 'husd', 'hbsb', 'husm', 'host', 'kbag']

    def __init__(self, fs_obj):
        self.fs_obj = fs_obj

    def get_funsdk_flash_version_from_props(self, bld_props=None):
        """ This method takes the bld_props JSON and return the flash_sdk_version for this drop """

        sdk_version = bld_props['components']['funsdk_flash_images']
        return sdk_version

    def get_active_funsdk_version_from_dpu(self, f1_index=0):
        """ This method takes the dpu_index and get the running flash_sdk_version using dpcsh """

        result = None
        dpc_client = self.fs_obj.get_dpc_client(f1_index=f1_index, auto_disconnect=True, statistics=True)
        cmd = "config/chip_info"
        dpc_result = dpc_client.json_execute(verb="peek", data=cmd, command_duration=3)
        if dpc_result["status"]:
            result = dpc_result["data"]["images"]
        return result

    #should return True or False
    def validate_firmware(self, f1_index=0, bld_props=None):
        """ This method takes the above methods and assert if entities are not equal.
            Currently We are just checking the main 4CC components which are updated during the upgrade process
            e.g eepr or emmc is not checked """

        sdk_version = self.get_funsdk_flash_version_from_props(bld_props)
        images = self.get_active_funsdk_version_from_dpu(f1_index)
        if not images:
            return False
        true_or_false = []
        for name in self.images_to_check:
            running_version = images[name]['active']['version']
            fun_test.log("Comparing ... image={}, running_version={}, should have version={}".format(name,
                                                                                                     running_version,
                                                                                                     sdk_version))
            true_or_false.append(running_version == int(sdk_version))

        return_code = True if all(true_or_false) else False
        return return_code
