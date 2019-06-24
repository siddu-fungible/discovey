import sys
import pexpect
import re

#usage example python clearline_cyclades.py <terminal-server> <terminal-port>
#python clearline_cyclades.py 10.1.23.154 2009

HOST = sys.argv[1]
LINE = sys.argv[2]

minus = 7000 if '70' in LINE else 2000
PORT = "%s" % (int(LINE) - minus)

print "Clearing terminal line ... ", HOST, LINE

child = pexpect.spawn('telnet -l admin {}'.format(HOST))
child.logfile = sys.stdout
child.expect("Password: ")
child.send("cyclades\r")
child.expect("$")
child.send("CLI\r")
child.expect("cli>")
child.send("administration sessions kill %s\r" % PORT)
child.expect("cli>")
child.send("quit\r")
child.expect("$")
child.send("exit\r")
print "line %s clear done ..." % LINE
