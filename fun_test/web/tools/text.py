#!/usr/bin/python

import socket
import time
import sys
import thread


#start dpc shell: "./dpcsh --tcp_proxy 5001"  and this will connect to that.

# Create a TCP socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

def read_and_print():
        chunk = 1024
        buffer = sock.recv(chunk)
        buffering = True
        while buffering:
                if "\n" in buffer:
                        (line, buffer) = buffer.split("\n", 1)
                        print line
                else:
                        more = sock.recv(chunk)
                        if not more:
                                buffering = False
                        else:
                                buffer += more
        if buffer:
                print buffer

# Connect the socket to the port where the server is listening
#server_address = ('10.138.0.3', int(sys.argv[1]))
server_address =  '/tmp/funos-dpc-text.sock'

try:
    sock.connect(server_address)
except socket.error, msg:
    print msg
    sys.exit(1)

thread.start_new_thread(read_and_print, ())

sock.sendall('echo "hello DPC!"\n')
sock.sendall("help\n")
sock.sendall("fibo 10\n")
sock.sendall("setenv $foo {x: y}\n")
sock.sendall("getenv $foo\n")
sock.sendall("peek stats\n")
sock.sendall('echo "all done!"\n')

time.sleep(2) # important because otherwise the print thread dies too early

