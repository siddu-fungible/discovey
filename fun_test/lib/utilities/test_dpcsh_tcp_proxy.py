#!/usr/bin/python

import socket, fcntl, errno
import time, json
import sys, os


class DpcshClient:
    def __init__(self, server_address, server_port=5001):
        self.server_address = server_address
        self.server_port = server_port
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

    '''
    def _read(self, expected_command_duration=1):
        start = time.time()
        chunk = 1024

        output = ""
        while True:
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

    '''

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
                    print("Some Error:" + str(e))
                    sys.exit(1)
            else:
                output += buffer
        return output

    def _connect(self):
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to {} {}".format(self.server_address, self.server_port))
            self.sock.connect((self.server_address, self.server_port))
            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def command(self, command, expected_command_duration=2):
        result = {"status": False, "data": None, "error_message": None, "command": command}
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
        return result

    def print_result(self, result):
        print "Command: {}".format(result["command"])
        print "Status: {}".format(result["status"])
        print json.dumps(result["data"], indent=4)

if __name__ == "__main__":
    dpcsh_client_obj = DpcshClient(server_address="10.1.20.67", server_port=20020)
    result = dpcsh_client_obj.command(command="peek stats")
    if result["status"]:
        dpcsh_client_obj.print_result(result=result)

    #result = dpcsh_client_obj.command(command="peek stats", expected_command_duration=3)
    #if result["status"]:
    #    dpcsh_client_obj.print_result(result=result)

    #result = dpcsh_client_obj.command(command="peek stats", expected_command_duration=3)
    #i = 0
    '''
    result = dpcsh_client_obj.command(command="peek stats/likv", expected_command_duration=3)
    dpcsh_client_obj.print_result(result)
    '''
