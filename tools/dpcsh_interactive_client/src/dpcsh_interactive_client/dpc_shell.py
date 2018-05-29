import os
import sys
import re
import time
import json

try:
    sdkdir = "/bin/" + os.uname()[0]
    if ("SDKDIR" in os.environ):
        sys.path.append(os.environ["SDKDIR"] + sdkdir)
    elif ("WORKSPACE" in os.environ):
        sys.path.append(os.environ["WORKSPACE"] + "/FunSDK/" + sdkdir)
    else:
        raise RuntimeError("Please specify WORKSPACE or SDKDIR environment variable")

    import dpc_client
except ImportError as ex:
    print "Failed to import dpc_client ensure FunSDK repo is clone under WORKSPACE dir"
    sys.exit(1)
except Exception as ex:
    print ex
    sys.exit(1)


class DpcShell(object):
    def __init__(self, target_ip, target_port, verbose=False):
        self.prompt = "(dpcsh) "
        self.target_ip = target_ip
        self.target_port = target_port
        print "Connecting to DPC server..."
        self.dpc_client = dpc_client.DpcClient(unix_sock=False, server_address=(target_ip, target_port))
        self.dpc_client.__verbose = verbose
        self.sock = self.dpc_client._DpcClient__sock
        # Ensure DPC tcp_proxy is connected
        self._ensure_connect()

    def _ensure_connect(self):
        result = self.dpc_client.execute(verb="echo", arg_list=["hello"])
        if result != 'hello':
            print 'Connection to DPC server via tcp_proxy at %s:%s failed. ' % (
                self.target_ip, self.target_port)
            sys.exit(1)
        else:
            print 'Connected to DPC server via tcp_proxy at %s:%s.' % (
                self.target_ip, self.target_port)














