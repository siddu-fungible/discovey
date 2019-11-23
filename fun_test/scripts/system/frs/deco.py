from lib.system.fun_test import *
from start_traffic import *


class ParsingFunos(FrsTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(ParsingFunos, self).setup()

    def run(self):
        self.func_rang(f1=0)

    def stats_deco(func):
        def function_wrapper(self, *args, **kwargs):
            come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                               ssh_username=self.fs['come']['mgmt_ssh_username'],
                               ssh_password=self.fs['come']['mgmt_ssh_password'])
            func(self, come_handle, kwargs["f1"])
            come_handle.destroy()
            return
        return function_wrapper

    @stats_deco
    def func_rang(self, come_handle, f1):
        pass
        come_handle.command("pwd")

    def create_files_based_on_the_stats(self):
        pass

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ParsingFunos())
    myscript.run()