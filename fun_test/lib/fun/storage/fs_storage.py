from lib.system.fun_test import fun_test


class FsStorage:
    def __init__(self, fs_obj):
        self.fs_obj = fs_obj

    def nvme_ssds(self, f1_index=0):
        result = None
        dpc_client = self.fs_obj.get_dpc_client(f1_index=f1_index, auto_disconnect=True, statistics=True)
        cmd = "storage/devices/nvme/ssds"
        dpc_result = dpc_client.json_execute(verb="peek", data=cmd, command_duration=3)
        if dpc_result["status"]:
            result = dpc_result["data"]
        return result

    def check_ssd_status(self, num_ssds, with_error_details=False):
        result = True
        error_message = ""
        fun_test.log("Checking if SSD's are present and online")
        ssd_present_count = 0
        for f1_index in range(self.fs_obj.NUM_F1S):
            if f1_index == self.fs_obj.disable_f1_index:
                continue
            ssd_info_f1 = self.nvme_ssds(f1_index)
            ssd_present_count += len(ssd_info_f1)
        if ssd_present_count != num_ssds:
            error_message += "Expected ssds: {}, actual ssds: {}".format(num_ssds, ssd_present_count)
        if with_error_details:
            result = result, error_message
        return result
