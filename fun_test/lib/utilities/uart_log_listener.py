import argparse
import socket
import select
import time
import sys
import signal
import threading


READ_BUF_SIZE = 16384
class Listener:
    def __init__(self, ip, port, output_file=None):
        self.buffer = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.original_sig_int_handler = None
        if threading.current_thread().__class__.__name__ == '_MainThread':
            self.original_sig_int_handler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self.exit_gracefully)
        self.terminate = None
        self.fh = sys.stdout
        if output_file:
            self.fh = open(output_file, "w")
            # Let it crash

        self.socket.connect((ip, port))
        print ("Connected to {}:{}".format(ip, port))

    def read_until(self, expected_data, timeout=1):
        self.buffer = ""
        if timeout:
            self.socket.settimeout(timeout)
        return_from_function = False
        while not return_from_function:
            try:
                readable, writable, exceptional = select.select(
                    [self.socket], [], [], timeout)
                return_from_function = False
                for s in readable:
                    if timeout:
                        self.socket.settimeout(timeout)
                    new_data = s.recv(READ_BUF_SIZE)
                    self.buffer += new_data
                    while new_data and expected_data not in self.buffer:
                        if timeout:
                            # print ("Setting timeout")
                            self.socket.settimeout(timeout)
                        try:
                            new_data = s.recv(READ_BUF_SIZE)
                        except socket.timeout:
                            # print "socket timeout"
                            break
                        self.buffer += new_data

                    self.fh.write(self.buffer)
                    self.fh.flush()

                    if expected_data in self.buffer:
                        return_from_function = True
                        self.buffer = ""
                        break
                    self.buffer = ""

            except Exception as ex:
                print ex

            time.sleep(0.000001)
        return self.buffer

    def exit_gracefully(self, sig, _):
        signal.signal(signal.SIGINT, self.original_sig_int_handler)
        self.fh.write(self.buffer)
        self.fh.close()
        sys.exit(-1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UART redirect")
    parser.add_argument('--proxy_port', dest="proxy_port", help="pyserial tcp proxy port")
    parser.add_argument('--output_file', default=None)
    args = parser.parse_args()
    proxy_port = args.proxy_port
    output_file = args.output_file
    print "Proxy port: {}".format(proxy_port)
    print "Output file: {}".format(output_file)
    nc = Listener(ip="127.0.0.1", port=int(proxy_port), output_file=output_file)
    nc.read_until("C0smic0Ceun")