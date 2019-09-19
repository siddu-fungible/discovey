import serial
from serial import Serial
import select
import argparse
import signal


class Listener():
    READ_BUFFER_SIZE = 1024

    def __init__(self, device_path, baud_rate, output_file_path=None):
        self.device_path = device_path
        self.baud_rate = baud_rate
        self.handle = None
        self.buffer = ""
        self.stopped = False
        self.read_counter = 0
        self.output_file_path = output_file_path
        self.output_file = open(self.output_file_path, "w+")

        self.original_sig_int_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.exit_gracefully)

    def exit_gracefully(self, *args, **kwargs):
        self.stop()
        print ("Exiting gracefully")
        signal.signal(signal.SIGINT, self.original_sig_int_handler)
        exit(0)

    def start(self):
        self.handle = serial.Serial(port=self.device_path, baudrate=self.baud_rate, timeout=1)
        self.handle.nonblocking()
        while not self.stopped and self.handle.isOpen():
            """
            try:
                self.handle.nonblocking()
                avail_read_sockets, avail_write, avail_error = select.select([self.handle], [], [], 1)
                for socket in avail_read_sockets:
                    self.buffer += socket.read(self.READ_BUFFER_SIZE)
                    self.write_to_file()
                    print self.buffer
            except Exception as ex:
                print (str(ex))
            """
            in_waiting_bytes = self.handle.inWaiting()
            if in_waiting_bytes > 0:
                self.buffer += self.handle.read(in_waiting_bytes)
                self.write_to_file(flush=True)

    def write_to_file(self, flush=True):
        self.output_file.write(self.buffer)
        if flush:
            self.output_file.flush()
        self.buffer = ""

    def stop(self):
        self.stopped = True
        if self.handle:
            self.handle.close()
            print ("Closing handle")
        self.write_to_file(flush=True)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UART log listener")
    parser.add_argument('--output_file', default=None)
    parser.add_argument('--device_path', default=None)
    parser.add_argument('--baud_rate', default=1000000)
    args = parser.parse_args()
    device_path = args.device_path
    output_file_path = args.output_file
    baud_rate = args.baud_rate
    listener = Listener(device_path=device_path, baud_rate=baud_rate, output_file_path=output_file_path)
    listener.start()
    listener.stop()