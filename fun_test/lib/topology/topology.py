from lib.system.utils import ToDictMixin

class ExpandedTopology(ToDictMixin):
    TO_DICT_VARS = ["duts"]
    def __init__(self):
        self.duts = {}
        self.tgs = {}

    def get_dut(self, index):
        result = None
        if index in self.duts:
            result = self.duts[index]
        return result

    def get_tg(self, index):
        result = None
        if index in self.tgs:
            result = self.tgs[index]
        return result

    def get_dut_instance(self, index):
        result = None
        dut = self.get_dut(index=index)
        if dut:
            result = dut.get_instance()
        return result

    def get_host_instance(self, dut_index, interface_index, host_index):
        dut = self.get_dut(index=dut_index)
        return dut.get_host_on_interface(interface_index=interface_index, host_index=host_index)

    def get_tg_instance(self, tg_index):
        tg = self.get_tg(index=tg_index)
        return tg.get_instance()