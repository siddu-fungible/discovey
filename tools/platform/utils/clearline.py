import sys
import pexpect
import re

HOST = sys.argv[1]
LINE = sys.argv[2]

PORT = "%s" % (int(LINE) - 2000)

print "Clearing terminal line ... ", HOST, LINE

child = pexpect.spawn('telnet {}'.format(HOST))
child.logfile = sys.stdout
child.expect ('#')
child.send("en\r")
child.expect("Password:")
child.send("cisco\r")
child.expect("#")
regex = re.compile('\n\*\s+%s' % PORT)

while True:
    child.send("show line\r")
    i = child.expect(["--More--", "#"])
    if i == 0:
        child.send("\r")
    else:
        child.send("\r")
    
    O = child.before
    print O
    if regex.findall(O):
        print "patter found ..."
        child.send("\r")
        child.expect("#")
        child.send("clear line %s\r" % PORT)
        child.expect("[confirm]")
        child.send("y")
        child.expect("#")
    else:
        child.send("exit\r")
        break

print "line clear done ..."
