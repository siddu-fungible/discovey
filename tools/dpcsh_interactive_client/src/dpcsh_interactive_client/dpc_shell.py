import os
import sys
import socket
import time
import json
from dpc_client import DpcClient
try:
    sdkdir = "/bin/" + os.uname()[0]
    if ("SDKDIR" in os.environ):
        sys.path.append(os.environ["SDKDIR"] + sdkdir)
    elif ("WORKSPACE" in os.environ):
        sys.path.append(os.environ["WORKSPACE"] + "/FunSDK/" + sdkdir)
    else:
        raise RuntimeError("Please specify WORKSPACE or SDKDIR environment variable")

    # import dpc_client
except ImportError as ex:
    print "Failed to import dpc_client ensure FunSDK repo is clone under WORKSPACE dir"
    sys.exit(1)
except Exception as ex:
    print ex
    sys.exit(1)


class DpcShell(object):
    def __init__(self, target_ip, target_port, verbose=False):
        self.target_ip = target_ip
        self.target_port = target_port
        print "Connecting to DPC server..."
        self.dpc_client = DpcClient(target_ip=target_ip, target_port=target_port, verbose=verbose)
        # self.dpc_client.set_verbose()
        # Ensure DPC tcp_proxy is connected

    '''
    def _ensure_connect(self, print_msg=True):
        result = self.dpc_client.execute(verb="echo", arg_list=["hello"])
        if result != 'hello':
            print 'Connection to DPC server via tcp_proxy at %s:%s failed. ' % (
                    self.target_ip, self.target_port)
            sys.exit(1)
        else:
            if print_msg:
                print 'Connected to DPC server via tcp_proxy at %s:%s.' % (
                    self.target_ip, self.target_port)
            self._set_syslog_level(level=3)

    def _set_syslog_level(self, level):
        try:
            result = self.dpc_client.execute(verb="poke", arg_list=["params/syslog/level", level])
            if result:
                print "Syslog level set to %d" % level
            else:
                print "Unable to set syslog level"
        except Exception as ex:
            print "ERROR: %s" % str(ex)
    '''
