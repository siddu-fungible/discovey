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
