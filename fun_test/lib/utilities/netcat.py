import socket

class Netcat:
    def __init__(self, ip, port):
        self.buff = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))

    def read(self, length=1024):
        return self.socket.recv(length)

    def read_until(self, data, timeout=None):
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

    def write(self, data):
        self.socket.send(data)

    def close(self):
        self.socket.close()

if __name__ == "__main__":
    nc = Netcat(ip="10.1.20.149", port=9990)
    nc.write("lfw; lmpg; ltrain; lstatus\n")
    print nc.read_until("f1 #")
