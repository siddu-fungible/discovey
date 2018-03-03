from lib.system.fun_test import *
import zmq
import time
import json
import Queue
import sys

POLL_TIMEOUT = 5000


def check_remote_command_result(out, commands):
    if not out:
        if 'tgen' in commands[0]:
            return
        fun_test.log('Possible ZMQ timeout while executing %s:' % commands)
        return

    command = out[0]['results'][0]['command']
    error = out[0]['results'][0]['error']
    if error:
        if 'docker unpause' not in command and 'add-port' not in command:
            fun_test.log('Remote command execution failed for command %s with error %s:' % (command, error))


def exec_remote_kill(commands, result=None, timeout=120):
    context = zmq.Context()

    poll = zmq.Poller()
    sockets = {}

    # Dictionary to group commands by VM IP
    ip_grouped_commands = {}
    for address, command in commands:
        ip_grouped_commands.setdefault(address, []).append(
            [command])

    for address, commands in ip_grouped_commands.items():
        ucast_socket = context.socket(zmq.REQ)
        ucast_socket.set(zmq.LINGER, 0)
        ucast_socket.connect('tcp://%s:93' % address)
        poll.register(ucast_socket, zmq.POLLIN)
        sockets[ucast_socket] = address
        ucast_socket.send_json(commands)

    deadline = time.time() + timeout

    while sockets and (timeout == 0 or time.time() < deadline):
        for socket, event in poll.poll(POLL_TIMEOUT):
            if event & zmq.POLLIN:
                address = sockets.pop(socket, None)
                if address is None:
                    continue
                response = socket.recv_json()
                response['address'] = address
                result.append(response)
    return result


def exec_send_file(commands, result=None, timeout=10, q=Queue.Queue()):
    context = zmq.Context()

    poll = zmq.Poller()
    sockets = {}

    ip_grouped_commands = {}
    for address, command in commands:
        ip_grouped_commands.setdefault(address, []).append(
            command)

    for address, commands in ip_grouped_commands.items():
        ucast_socket = context.socket(zmq.REQ)
        ucast_socket.set(zmq.LINGER, 0)
        ucast_socket.connect('tcp://%s:92' % address)
        poll.register(ucast_socket, zmq.POLLIN)
        sockets[ucast_socket] = address
        ucast_socket.send_json(commands)

    deadline = time.time() + timeout

    while sockets and (timeout == 0 or time.time() < deadline):
        for socket, event in poll.poll(POLL_TIMEOUT):
            if event & zmq.POLLIN:
                address = sockets.pop(socket, None)
                if address is None:
                    continue
                response = socket.recv_json()
                response['address'] = address
                result.append(response)

    q.put(result)
    check_remote_command_result(result, commands)
    return result


def exec_remote_commands(commands, result=None, timeout=10, q=Queue.Queue()):
    context = zmq.Context()
    poll = zmq.Poller()
    sockets = {}

    ip_grouped_commands = commands
    for address, commands in ip_grouped_commands:
        ucast_socket = context.socket(zmq.REQ)
        ucast_socket.set(zmq.LINGER, 0)
        ucast_socket.connect('tcp://%s:90' % address)
        poll.register(ucast_socket, zmq.POLLIN)
        sockets[ucast_socket] = address
        ucast_socket.send_json(commands)

    deadline = time.time() + timeout
    while sockets and (timeout == 0 or time.time() < deadline):
        for socket, event in poll.poll(POLL_TIMEOUT):
            if event & zmq.POLLIN:
                address = sockets.pop(socket, None)
                if address is None:
                    continue
                response = socket.recv_json()
                response['address'] = address
                result.append(response)

    q.put(result)
    check_remote_command_result(result, commands)
    return result 

