import serial
import sys
import time
import argparse


class F1UBootInterface:
    PROMPT_TERMINATOR = "f1 #"

    def __init__(self, device_path, speed):
        self.device_path = device_path
        self.speed = speed

    def open(self):
        self.handle = serial.Serial(self.device_path, self.speed)

    def close(self):
        self.handle.close()

    def write(self, data):
        self.handle.write(data + "\r")
        sys.stdout.write(data + "\n")
        sys.stdout.flush()

    def read_all(self, timeout=5):
        self.handle.timeout = timeout
        start = time.time()
        s = ""
        while True:
            bytes_to_read = self.handle.inWaiting()
            new_data = self.handle.read(bytes_to_read)
            sys.stdout.write(new_data)
            sys.stdout.flush()
            s += new_data
            now = time.time()
            if (now - start) > timeout or (self.PROMPT_TERMINATOR in s):
                break
        return s

    def flush(self):
        self.write("")
        self.read_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F1 U-boot interface")
    parser.add_argument('--device_path', dest="device_path")
    parser.add_argument('--speed', dest="speed")
    parser.add_argument('--command', dest="command")
    parser.add_argument('--timeout', dest="timeout", default=15)
    args = parser.parse_args()

    u_boot_interface = F1UBootInterface(device_path=args.device_path, speed=int(args.speed))
    u_boot_interface.open()
    u_boot_interface.flush()
    u_boot_interface.write(args.command)
    output = u_boot_interface.read_all(timeout=int(args.timeout))
    print output
    u_boot_interface.close()