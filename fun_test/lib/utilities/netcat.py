from lib.system.fun_test import fun_test, FunTimer
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
        max_wait_timer = FunTimer(max_time=timeout)
        while not fun_test.closed and expected_data not in self.buffer and not self.terminate and not return_from_function and not max_wait_timer.is_expired():
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

    nc = Netcat(ip="10.1.105.166", port=9990)
    nc.write("setenv autoload no\n")
    print nc.read_until("f1 #")
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
    nc.write("setenv gatewayip 10.1.105.1\n")
    print nc.read_until("f1 #")
    nc.write("setenv serverip 10.1.21.48\n")
    print nc.read_until("f1 #")
    nc.write("setenv bootargs sku=SKU_FS1600_0 app=hw_hsu_test cc_huid=3 module_log=epcq:DEBUG,virtual_interface:DEBUG --all_100g --disable-wu-watchdog --dpc-server --dpc-uart retimer=0,1,2\n")
    print nc.read_until("f1 #")
    nc.write("dhcp\n")
    print nc.read_until("f1 #")
    nc.write("tftpboot 0xa800000080000000 10.1.21.48:s_16365_funos-f1.stripped.gz\n")
    print nc.read_until("f1 #")
    nc.write("unzip 0xa800000080000000 0xffffffff99000000;\n")
    print nc.read_until("f1 #")
    nc.write("bootelf -p 0xffffffff99000000\n")
    print nc.read_until("f1 #")

    nc = Netcat(ip="10.1.105.166", port=9991)
    nc.write("setenv autoload no\n")
    print nc.read_until("f1 #")
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
    nc.write("setenv gatewayip 10.1.105.1\n")
    print nc.read_until("f1 #")
    nc.write("setenv serverip 10.1.21.48\n")
    print nc.read_until("f1 #")
    nc.write("setenv bootargs sku=SKU_FS1600_1 app=hw_hsu_test cc_huid=3 module_log=epcq:DEBUG,virtual_interface:DEBUG --all_100g --disable-wu-watchdog --dpc-server --dpc-uart retimer=0,1,2\n")
    print nc.read_until("f1 #")
    nc.write("dhcp\n")
    print nc.read_until("f1 #")
    nc.write("tftpboot 0xa800000080000000 10.1.21.48:s_16365_funos-f1.stripped.gz\n")
    print nc.read_until("f1 #")
    nc.write("unzip 0xa800000080000000 0xffffffff99000000;\n")
    print nc.read_until("f1 #")
    nc.write("bootelf -p 0xffffffff99000000\n")
    print nc.read_until("f1 #")