from lib.system.fun_test import *
from scripts.networking.helper import *
from lib.fun.fs import *


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Get FS system : %s credentials, image and bootargs "
                              % fun_test.get_job_environment_variable('test_bed_type'))

    def setup(self):
        global fs
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get()
        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")

    def cleanup(self):
        pass


class BootFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary=" Boot FS",
                              steps="""
                              1. Boot up FS system : %s
                              """ % fun_test.get_job_environment_variable('test_bed_type'))

    def setup(self):
        pass

    def run(self):
        fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BootFS())
