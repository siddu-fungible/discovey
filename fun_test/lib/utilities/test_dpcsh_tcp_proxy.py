#!/usr/bin/python

import socket, fcntl, errno
import time, json
import sys, os


def read(sock, timeout=3):
    start = time.time()
    chunk = 1024

    output = ""
    while True:
        elapsed_time = time.time() - start
        if elapsed_time > timeout:
            break
        try:
            buffer = sock.recv(chunk)
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                time.sleep(0.2)
                continue
            else:
                # a "real" error occurred
                print e
                sys.exit(1)
        else:
            output += buffer
    return output


def dpc_command(server_address, port, command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (server_address, port)

    try:
        sock.connect(server_address)
        fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
    except socket.error, msg:
        print msg
        sys.exit(1)

    sock.sendall("{}\n".format(command))
    output = read(sock=sock)
    print "O:" + output + ":E"
    result = json.loads(output)
    return result

if __name__ == "__main__":
    dpc_command(server_address="10.1.20.67", port=5001, command="peek stats")