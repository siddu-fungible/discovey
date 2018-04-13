import subprocess
import os


# compress file
class TestCompression:
    def __init__(self, log_file=None):
        self.log_file = log_file if log_file else "/tmp/output.txt"
        self.log_file_obj = open(self.log_file, 'w')
        self.compressor_binary = "/Users/aameershaikh/projects/accel-compression/text/compressor"

    def log(self, data):
        print data
        self.log_file_obj.write(data + "\n")

    def size_of_file(self, file_name):
        return os.path.getsize(file_name)

    def execute_command(self, *cmd):
        self.log("Executing command: {}".format(' '.join(cmd)))
        cmd = list(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()
        self.log("Output: {0}\nError: {1}".format(output[0], output[1]))
        if output[1]:
            ex_messag = "Command failed with error: {0}".format(output[1])
            self.log(ex_messag)
            raise Exception(ex_messag)
        return output

    def compare_files(self, file1, file2):
        resp = self.execute_command("diff", file1, file2)
        if resp[0].strip():
            self.log("Diff Output: {}".format(resp[0]))
            return False
        return True
