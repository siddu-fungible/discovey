from lib.system.fun_test import FunTestLibException, fun_test
import json, time
import socket, fcntl, errno
import os, sys

class StorageController():
    def __init__(self, target_ip=None, target_port=None):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = None

    def sendall(self, data, expected_command_duration=1):
        start = time.time()
        while data:
            elapsed_time = time.time() - start
            if elapsed_time > expected_command_duration:
                break
            try:
                sent = self.sock.send(data)
                data = data[sent:]
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(0.1)
                    continue


    def _read(self, expected_command_duration=1):
        start = time.time()
        chunk = 1024

        output = ""
        while not output.endswith("\n"):
            elapsed_time = time.time() - start
            if elapsed_time > expected_command_duration:
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
                    print e
                    sys.exit(1)
            else:
                output += buffer
        return output

    def _connect(self):
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to {} {}".format(self.target_ip, self.target_port))
            self.sock.connect((self.target_ip, self.target_port))
            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def command(self, command, expected_command_duration=2):
        result = {"status": False, "data": None, "error_message": None, "command": command}
        output = ""
        try:
            self._connect()
            # print ("Sending:" + command + "\n")
            self.sendall("{}\n".format(command))
            output = self._read(expected_command_duration)
            json_output = json.loads(output)
            result["status"] = True
            result["data"] = json_output
            result["error_message"] = None

        except socket.error, msg:
            print msg
            result["error_message"] = msg
        except Exception as ex:
            print (str(ex))
            print ("result from read:" + str(output))
            result["error_message"] = str(ex)
        if not result["status"]:
            fun_test.log("Command failed: " + fun_test.dict_to_json_string(result))
        return result

    def print_result(self, result):
        print "Command: {}".format(result["command"])
        print "Status: {}".format(result["status"])
        print json.dumps(result["data"], indent=4)

    def json_command(self, d):
        return self.command('storage {}'.format(json.dumps(d)))

    def ip_cfg(self, ip):
        cfg_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip":ip}}
        return self.json_command(cfg_dict)

    def create_blt_volume(self,
                          capacity,
                          uuid,
                          block_size,
                          name):
        create_dict = {}
        create_dict["class"] = "volume"
        create_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
        create_dict["params"] = {}
        create_dict["params"]["type"] = "VOL_TYPE_BLK_LOCAL_THIN"
        create_dict["params"]["capacity"] = capacity
        create_dict["params"]["block_size"] = block_size
        create_dict["params"]["uuid"] = uuid
        create_dict["params"]["name"] = name
        return self.json_command(create_dict)



if __name__ == "__main__":
    sc = StorageController(target_ip="10.1.20.67", target_port=40220)
    output = sc.command("peek stats")
    sc.print_result(output)