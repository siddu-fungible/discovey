import subprocess

class TaskTemplate:

    def __init__(self):
        pass

    def call(self, command, shell=True):
        output = subprocess.call(command, shell=shell)
        return output

    def popen(self, command, args):
        p = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        return_code = p.returncode
        return return_code, output, err

if __name__ == "__main__":
    t = TaskTemplate()
    t.call("ls -l")
    return_code, output, err = t.popen(command="docker", args=["ps", "-a"])
    print output
