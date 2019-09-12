import subprocess

class TaskTemplate:

    def __init__(self):
        pass

    def call(self, command, shell=True):
        output = subprocess.call(command, shell=shell)
        return output

    def popen(self, command, args, shell=None):
        p = subprocess.Popen([command] + args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        output, err = p.communicate()
        return_code = p.returncode
        return return_code, output, err

    def piped_commands(self, commands):
        previous_proc = None
        for index, command in enumerate(commands):
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
            stdin = subprocess.PIPE
            if previous_proc:
                stdin = previous_proc.stdout
            proc = subprocess.Popen(command.split(), stdin=stdin, stdout=stdout, stderr=stderr)
            previous_proc = proc

        output = err = None
        return_code = -1
        if previous_proc:
            output, err = previous_proc.communicate()
            return_code = previous_proc.returncode
        return return_code, output, err

if __name__ == "__main__":
    t = TaskTemplate()
    t.call("ls -l")
    return_code, output, err = t.popen(command="docker", args=["ps", "-a"])
    print output
