from fun_global import get_current_time, get_localized_time
import subprocess
import os
import datetime
from datetime import timedelta

class TaskTemplate:

    def __init__(self):
        pass

    def call(self, command, shell=True, working_directory=None):
        output = subprocess.call(command, shell=shell, cwd=working_directory)
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


    def list_files_by_time(self, directory, from_time=None, to_time=None):
        result = []
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                path = os.path.join(root, file_name)
                st = os.stat(path)
                modified_time = get_localized_time(datetime.datetime.fromtimestamp(st.st_mtime))
                if from_time:
                    if modified_time < from_time:
                        continue
                if to_time:
                    if modified_time > to_time:
                        continue
                result.append(path)
        return result

    def get_file_size(self, file_name):
        result = None
        if os.path.exists(file_name):
            st = os.stat(file_name)
            result = st.st_size
        return result

if __name__ == "__main__":
    t = TaskTemplate()
    files = t.list_files_by_time(directory="/tmp", from_time=get_current_time() - timedelta(days=30))
    files = t.list_files_by_time(directory="/tmp", from_time=get_current_time() - timedelta(days=1))

    for f in files:
        t.get_file_size(file_name=f)
    # t.call("ls -l")
    #return_code, output, err = t.popen(command="docker", args=["ps", "-a"])
    #print output
