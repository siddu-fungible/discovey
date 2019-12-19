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
        self.stop_reading_trigger = False

    def read(self, length=1024):
        return self.socket.recv(length)

    def read_until(self, expected_data, timeout=15, write_on_trigger=None, read_buffer=1024):
        self.stop_reading_trigger = False
        self.buffer = ""
        if timeout:
            self.socket.settimeout(timeout)
        return_from_function = False
        max_wait_timer = FunTimer(max_time=timeout)
        while not self.stop_reading_trigger and not fun_test.closed and expected_data not in self.buffer and not self.terminate and not return_from_function and not max_wait_timer.is_expired():
            try:
                readable, writable, exceptional = select.select(
                    [self.socket], [], [], timeout)
                return_from_function = False
                for s in readable:
                    if timeout:
                        self.socket.settimeout(timeout)
                    new_data = s.recv(read_buffer)
                    self.buffer += new_data
                    while new_data and expected_data not in self.buffer:
                        if timeout:
                            self.socket.settimeout(timeout)
                        new_data = s.recv(read_buffer)
                        self.buffer += new_data
                        if write_on_trigger:
                            # remove_list = []
                            for key, value in write_on_trigger.iteritems():
                                if key in self.buffer:
                                    self.write(value)
                                    fun_test.log("==> {}".format(value))
                                    # remove_list.append(key)
                            # for key in remove_list:
                            #    del write_on_trigger[key]
                    if not new_data or expected_data in self.buffer:
                        return_from_function = True
                        break

            except Exception as ex:
                break

            time.sleep(0.00001)
        self.stop_reading_trigger = False
        return self.buffer

    def stop_reading(self):
        self.stop_reading_trigger = True

    def get_buffer(self):
        buffer = self.buffer
        self.clear_buffer()
        return buffer

    def clear_buffer(self):
        self.buffer = ""

    def write(self, data):
        self.socket.send(data)

    def close(self):
        self.terminate = True
        self.socket.close()
        return self.buffer

if __name__ == "__main__":

    from lib.fun.fs import Fpga

    fpga_ip = "fs21-fpga.fungible.local"
    f = Fpga(host_ip=fpga_ip, ssh_username="root", ssh_password="root")
    f.reset_f1(0)

    tftp_image = "s_21048_funos-f1.stripped.gz"

    bmc_ip = "fs21-bmc.fungible.local"
    gateway_ip = "10.1.20.1"
    nc = Netcat(ip=bmc_ip, port=9990)
    nc.write("setenv autoload no\n")
    print nc.read_until("f1 #")
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
    #nc.write("setenv gatewayip {}\n".format(gateway_ip))
    print nc.read_until("f1 #")
    nc.write("setenv serverip 10.1.21.48\n")
    print nc.read_until("f1 #")
    nc.write("setenv bootargs sku=SKU_FS1600_0 app=load_mods --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g\n")

    print nc.read_until("f1 #")
    nc.write("dhcp\n")
    print nc.read_until("f1 #")
    nc.write("tftpboot 0xa800000080000000 10.1.21.48:{}\n".format(tftp_image))
    print nc.read_until("f1 #")
    nc.write("unzip 0xa800000080000000 0xffffffff99000000;\n")
    print nc.read_until("f1 #")
    nc.write("bootelf -p 0xffffffff99000000\n")
    print nc.read_until("f1 #", timeout=30)


    """

    bmc_ip = "fs21-bmc.fungible.local"
    gateway_ip = "10.1.20.1"
    nc = Netcat(ip=bmc_ip, port=9991)
    nc.write("setenv autoload no\n")
    print nc.read_until("f1 #")
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
    #nc.write("setenv gatewayip {}\n".format(gateway_ip))
    print nc.read_until("f1 #")
    nc.write("setenv serverip 10.1.21.48\n")
    print nc.read_until("f1 #")
    nc.write("setenv bootargs sku=SKU_FS1600_1 app=load_mods --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g\n")
    # nc.write("setenv bootargs sku=SKU_FS1600_0 app=load_mods --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g\n")

    print nc.read_until("f1 #")
    nc.write("dhcp\n")
    print nc.read_until("f1 #")
    nc.write("tftpboot 0xa800000080000000 10.1.21.48:s_19079_funos-f1.stripped.gz\n")
    print nc.read_until("f1 #")
    nc.write("unzip 0xa800000080000000 0xffffffff99000000;\n")
    print nc.read_until("f1 #")
    nc.write("bootelf -p 0xffffffff99000000\n")
    print nc.read_until("f1 #", timeout=30)
    """