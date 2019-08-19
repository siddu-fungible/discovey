from lib.system.fun_test import FunTestLibException, fun_test
import json, time, re
import socket, fcntl, errno
import os, sys


class DpcshClient(object):
    def __init__(self, mode="storage", target_ip=None, target_port=None, verbose=True, auto_disconnect=False):
        """

        :param mode:
        :param target_ip:
        :param target_port:
        :param verbose:
        :param auto_disconnect: If set dpcsh client will auto disconnect after each command
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = None
        self.mode = mode
        self.verbose = verbose
        self.auto_disconnect = auto_disconnect

    def sendall(self, data, command_duration=1):
        start = time.time()
        while data:
            elapsed_time = time.time() - start
            if elapsed_time > command_duration:
                break
            try:
                sent = self.sock.send(data)
                data = data[sent:]
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(0.1)
                    continue
                else:
                    fun_test.critical("DPCSH socket error: {}: {}".format(socket.error, e))

    def _read(self, command_duration=1, chunk=4096):
        start = time.time()

        output = ""
        while not output.endswith("\n"):
            elapsed_time = time.time() - start
            if elapsed_time > command_duration:
                fun_test.critical("Command timeout: Output: {}".format(output))
                break
            try:
                buffer = self.sock.recv(chunk)
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(0.1)
                    continue
                else:
                    # a "real" error occurred
                    fun_test.critical("DPCSH exception: {}".format(e))
                    break
            else:
                output += buffer
        if fun_test.get_job_environment_variable("dry_run"):
            if "\n" in output:
                fun_test.log("slash n in output. Output: S: {} xxx E".format(output))
        return output

    def _connect(self):
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fun_test.log("Connecting to {} {}".format(self.target_ip, self.target_port))
            self.sock.connect((self.target_ip, self.target_port))
            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def disconnect(self):
        if self.sock:
            self.sock.close()
        self.sock = None
        return True

    def command(self, command, legacy=False, command_duration=2, sleep_duration=0.1, chunk=4096):
        result = {"status": False, "data": None, "error_message": None, "command": command}
        output = ""
        try:
            self._connect()
            command = "{}\n".format(command)
            if legacy:
                command = "#!sh {}".format(command)
            if self.verbose:
                fun_test.log("DPCSH Send:" + command + "\n")

            self.sendall(command, command_duration)
            time.sleep(sleep_duration)
            output = self._read(command_duration, chunk)
            if output:
                actual_output = self._parse_actual_output(output=output)
                result["raw_output"] = output
                try:
                    json_output = json.loads(actual_output.strip())
                except:
                    fun_test.debug("Unable to parse JSON data")
                    json_output = output
                result["status"] = True

                if "result" in json_output:
                    result["data"] = json_output["result"]
                else:
                    result["data"] = json_output
                result["error_message"] = None
            if (type(result["data"]) is bool and result["data"] is False) \
                    or (type(result["data"]) is int and result["data"] < 0)\
                    or result["data"] is None:
                result["status"] = False
        except socket.error, msg:
            print msg
            result["error_message"] = msg
        except Exception as ex:
            print (str(ex))
            print ("result from read:" + str(output))
            result["error_message"] = str(ex)
        if not result["status"]:
            fun_test.log("Command failed: " + fun_test.dict_to_json_string(result))
        if self.verbose:
            self.print_result(result=result)
        if self.auto_disconnect:
            self.disconnect()
        return result

    def _parse_actual_output(self, output):
        actual_output = output
        if re.search(r'.*arguments.*', output, re.MULTILINE):
            actual_output = re.sub(r'.*arguments.*', "", output, re.MULTILINE)
        return actual_output

    def print_result(self, result):
        fun_test.log("DPCSH Result")
        fun_test.log("Command: {}".format(result["command"]))
        fun_test.log("Status: {}".format(result["status"]))
        fun_test.log("Data: {}". format(json.dumps(result["data"], indent=4)))
        fun_test.log("Raw output: {}".format(result["raw_output"]))

    def json_execute(self, verb, data=None, command_duration=1, sleep_duration=0.1, tid=0, chunk=4096):
        jdict = None
        if data:
            if type(data) is not list:
                jdict = {"verb": verb, "arguments": [data], "tid": tid}
            elif type(data) is list:
                jdict = {"verb": verb, "arguments": data, "tid": tid}
        else:
            jdict = {"verb": verb, "arguments": [], "tid": tid}

        return self.command('{}'.format(json.dumps(jdict)),
                            command_duration=command_duration, sleep_duration=sleep_duration, chunk=chunk)

    def json_command(self, data, action="", additional_info="", command_duration=1):
        return self.command('#!sh {} {} {} {}'.format(self.mode, action, json.dumps(data), additional_info),
                            command_duration=command_duration)


if __name__ == "__main__":
    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)
    d.json_execute(verb="perf", data="reinit", command_duration=4)
    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)

    d.json_execute(verb="perf", data="start", command_duration=4)
    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)

    d.disconnect()
    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)
    # d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220)

    d.json_execute(verb="peek", data="stats/vppkts", command_duration=4)
    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)

    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)
    d.json_execute(verb="perf", data="stop", command_duration=4)

    d = DpcshClient(target_ip="fs21-come.fungible.local", target_port=40220, auto_disconnect=True)
    d.json_execute(verb="perf", data="offload", command_duration=4)

    # d.command("peek help", legacy=False)