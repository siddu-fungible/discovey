from lib.system.fun_test import fun_test
import socket
import select
import time

class Netcat:
    def __init__(self, ip, port):
        self.buffer = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.terminate = None

    def read(self, length=1024):
        return self.socket.recv(length)

    def read_until2(self, data, timeout=None):
        if timeout:
            self.socket.settimeout(timeout)
        buf = ""
        try:

            while data not in buf:
                new_data = self.socket.recv(1024)
                buf += new_data
        except Exception as ex:
            pass
        return buf

    def read_until(self, expected_data, timeout=15):
        self.buffer = ""
        if timeout:
            self.socket.settimeout(timeout)
        return_from_function = False
        while not fun_test.closed and expected_data not in self.buffer and not self.terminate and not return_from_function:
            try:
                readable, writable, exceptional = select.select(
                    [self.socket], [], [], timeout)
                return_from_function = False
                for s in readable:
                    if timeout:
                        self.socket.settimeout(timeout)
                    new_data = s.recv(1024)
                    self.buffer += new_data
                    while new_data and expected_data not in self.buffer:
                        if timeout:
                            self.socket.settimeout(timeout)
                        new_data = s.recv(1024)
                        self.buffer += new_data
                    if not new_data or expected_data in self.buffer:
                        return_from_function = True
                        break

            except Exception as ex:
                break

            time.sleep(0.00001)
        return self.buffer

    def write(self, data):
        self.socket.send(data)

    def close(self):
        self.terminate = True
        self.socket.close()
        return self.buffer

if __name__ == "__main__":
    nc = Netcat(ip="10.1.20.149", port=9990)
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
