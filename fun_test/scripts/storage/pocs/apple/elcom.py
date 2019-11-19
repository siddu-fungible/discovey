import argparse
import sys
import os
import time
import pexpect
import telnetlib

class ElcomPowerSwitch:
    """
    ELCOM power outlet class
    """
    def __init__(self, hostname, userid, password):
        #Init Elcom Prompt
        self.prompt = "Elcom"
        #Connect to the PDU
        self.pducon = self.connect(hostname, userid, password)
        if self.pducon is None:
            print 'Connection to ELCOM PDU:%s Failed'%(hostname)
        else:
            print 'PDU Connection Success'

    def connect(self, ip, user, passwd):
        child = pexpect.spawn('telnet '+ip, timeout=500)
        child.expect('Username')
        child.sendline(user + "\r")
        child.expect('Password')
        child.sendline(passwd + "\r")
        child.expect(self.prompt)
        print "Login To ELCOM PDU succesfull"
        return child

    def switch(self, outlet, op):
        #Prepend a "0" in case it is not present
        if len(outlet) == 1:
            outlet= "0"+outlet
        else:
            if outlet.startswith("0") is False:
                outlet= "0"+outlet
        # It is assumed that now the prompt is at elcom CLI.
        try:
            i = self.pducon.expect([self.prompt, pexpect.TIMEOUT])
        except:
            print ('Did not Connect to PDU. Prompt not seen')
            print (self.pducon.before)
        if i == 0:
            #We reach here and connection is still up
            if op == "off":
                cmd = "outlet " + outlet + " " + "0"
            if op == "on":
                cmd = "outlet " + outlet + " " + "1"
        if i == 1:
            print 'Timeout at PDU Con Prompt'
            print self.pducon.before
            return
        #Execute command
        self.pducon.sendline(cmd + "\r")
        try:
            i = self.pducon.expect([self.prompt, pexpect.TIMEOUT])
        except:
            print 'Exception tryin outlet command'
            print self.pducon.before
            return
        #It seems that we have completed command.
        output =  self.pducon.before
        if output.rfind("OFF") >= 0:
            print 'Outlet OFF Success'
        if output.rfind("ON") >= 0:
            print 'Outlet ON Success'

    def off(self, outlet):
        """ Turn the outlet off """
        return self.switch(outlet, "off")

    def on(self, outlet):
        """ Turn the outlet on """
        return self.switch(outlet, "on")

    def close(self):
        """ Close connection """
        self.pducon.sendline("bye\r")
        child.expect("Connection closed")

#API
def pdu_operation(ip, user, pwd, op, outlet):
    print('Connecting to a ELCOM PowerSwitch at ip:%s user:%s op:%s outlet:%s'%(ip, user, op, outlet))
    switch = ElcomPowerSwitch(hostname=ip, userid=user, password=pwd)
    if op == "off":
        print("Turning off outlet:%s" % outlet)
        switch.off(outlet)

    if op == "on":
        print("Turning on outlet:%s" % outlet)
        switch.on(outlet)

if __name__ == "__main__":
    pswd = ""
    if sys.version_info[:2] == (2, 7):
        parser = argparse.ArgumentParser(description="option parser")
        parser.add_argument("-i", action="store", dest="hostip", help="IP address of PDU")
        parser.add_argument("-u", action="store", dest="username", help="PDU user name")
        parser.add_argument("-p", action="store", dest="password", help="PDU User password")
        parser.add_argument("-o", action="store", dest="operation", help="off|on")
        parser.add_argument("-t", action="store", dest="outlet", help="Outlet Number")
        args=parser.parse_args()
        if args.hostip:
            ip = args.hostip
        else:
            logger.debug("PDU needs IP");
        if args.username:
            user = args.username
        if args.password:
            pswd = args.password
        if args.operation:
            op = args.operation
        if args.outlet:
            out = args.outlet
    else:
        logger.debug("Detected PythonVersion != 2.7. If less than 2.7 Please use 2.7")
        sys.exit(0)
    # Do the operation
    pdu_operation(ip, user, pswd, op, out)