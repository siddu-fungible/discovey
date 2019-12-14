import os
from subprocess import Popen, PIPE
from lib.host.linux import Linux
from lib.system.fun_test import *
from lib.system import utils


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.switch_to_py3_env()

    def cleanup(self):
        pass

    def run(self):
        pass

    def initialize_json_data(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Input: {}".format(job_inputs))
        for k, v in job_inputs.iteritems():
            setattr(self, k, v)

    def initialize_variables(self):
        self.handle = Linux(host_ip="192.168.43.106", ssh_username="ranga", ssh_password="asdf")



    def switch_to_py3_env(self):
        self.handle.command("source /Users/ranga/mypython/bin/activate")
        self.handle.command("redfishtool -r 10.1.40.110 -u Administrator -p superuser -A Basic -S Always Chassis -1 Power")
        self.handle.command("redfishtool -r 10.1.40.110 -u Administrator -p superuser -A Basic -S Always Chassis -1 Thermal")
        # os.system("source ~/py3/bin/activate")
        # os.system("/bin/bash --rcfile ./set_env.sh")



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()