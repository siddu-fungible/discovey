import os
import serial
import sys
import time
import argparse


class UartListener:
    def __init__(self, device_path, speed, log_filename):
        self.device_path = device_path
        self.speed = speed
        self.log_filename = log_filename
        try:
            os.unlink(self.log_filename)
        except:
            pass

    def open(self):
        self.handle = serial.Serial(self.device_path, self.speed)

    def close(self):
        self.handle.close()

    def read_loop(self):
        os.system("stty -F {} {} -ocrnl -crtscts -echo".format(self.device_path, self.speed))
        while True:
            cmd = "cat {} >> {}".format(self.device_path, self.log_filename)
            print(cmd)
            os.system(cmd)
            time.sleep(1)

    def append_to_file(self, content):
        with open(self.log_filename, "a+") as f:
            f.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UART log listener")
    parser.add_argument('--device_path', dest="device_path")
    parser.add_argument('--speed', dest="speed")
    parser.add_argument('--log_filename', dest="log_filename")
    args = parser.parse_args()

    listener = UartListener(device_path=args.device_path, speed=int(args.speed), log_filename=args.log_filename)
    listener.open()
    listener.read_loop()
    listener.close()