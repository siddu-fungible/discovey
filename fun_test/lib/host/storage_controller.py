from lib.system.fun_test import FunTestLibException, fun_test
import json, time
import socket, fcntl, errno
import os, sys

class StorageController():
    def __init__(self, mode="storage", target_ip=None, target_port=None, verbose=True):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = None
        self.mode = mode
        self.verbose = verbose

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
            fun_test.log("Connecting to {} {}".format(self.target_ip, self.target_port))
            self.sock.connect((self.target_ip, self.target_port))
            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def command(self, command, expected_command_duration=2):
        result = {"status": False, "data": None, "error_message": None, "command": command}
        output = ""
        try:
            self._connect()
            if self.verbose:
                fun_test.log("DPCSH Send:" + command + "\n")
            self.sendall("{}\n".format(command))
            output = self._read(expected_command_duration)
            result["raw_output"] = output
            json_output = json.loads(output)
            result["status"] = True
            result["data"] = json_output
            result["error_message"] = None
            try:
                if int(result["data"]):
                    result["status"] = False
            except:
                pass
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
        return result

    def print_result(self, result):
        fun_test.log("DPCSH Result")
        fun_test.log("Command: {}".format(result["command"]))
        fun_test.log("Status: {}".format(result["status"]))
        fun_test.log("Data: {}". format(json.dumps(result["data"], indent=4)))
        fun_test.log("Raw output: {}".format(result["raw_output"]))

    def json_command(self, data, action="", additional_info=""):
        return self.command('{} {} {} {}'.format(self.mode, action, json.dumps(data), additional_info))

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

    def attach_volume(self, ns_id, uuid, remote_ip):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"huid": 0,
                                  "ctlid": 0,
                                  "fnid": 5,
                                  "nsid": ns_id,
                                  "uuid": uuid,
                                  "remote_ip": remote_ip}}
        return self.json_command(attach_dict)

    def create_rds_volume(self, capacity, block_size, uuid, name, remote_ip, remote_nsid):
        create_dict = {"class": "volume",
                       "opcode": "VOL_ADMIN_OPCODE_CREATE",
                       "params": {"type": "VOL_TYPE_BLK_RDS",
                                  "capacity": capacity,
                                  "block_size": block_size,
                                  "uuid": uuid,
                                  "name": name,
                                  "remote_ip": remote_ip,
                                  "remote_nsid": remote_nsid}}
        return self.json_command(create_dict)


    def create_replica_volume(self, capacity,
                              block_size,
                              uuid,
                              name,
                              pvol_id):
        create_dict = {"class": "volume",
                       "opcode": "VOL_ADMIN_OPCODE_CREATE",
                       "params": {"type": "VOL_TYPE_BLK_REPLICA",
                                  "capacity": capacity,
                                  "block_size": block_size,
                                  "uuid": uuid,
                                  "name": name,
                                  "min_replicas_insync": 1,
                                  "pvol_type": "VOL_TYPE_BLK_RDS",
                                  "pvol_id": pvol_id}}
        return self.json_command(create_dict)


if __name__ == "__main__":
    sc = StorageController(target_ip="10.1.20.67", target_port=40220)
    output = sc.command("peek stats")
    sc.print_result(output)