import sys
import time
import dlipower
import random

USER = "biji"
PASSWORD = "biji"

#usage example - python DLIwebpower-random.py <WEBPOWER-HOST> <POWER-PORT>
#python DLIwebpower-random.py 10.1.23.33 9

HOST = sys.argv[1]
PORT = int(sys.argv[2])
if (PORT < 1 ) or (PORT > 8):
	sys.exit("port out-of-range ...")

print('Connecting to a DLI WebPower PowerSwitch at %s' % HOST)
switch = dlipower.PowerSwitch(hostname=HOST, userid=USER, password=PASSWORD)

print('Turning off the outlet#%s' % PORT)
switch.off(PORT)

print('The powerstate of the outlet is currently', switch[PORT].state)
print('The current status of the powerswitch is:')
print(switch)

random_seconds = random.randint(5, 30)

print('Sleeping for %s seconds' % random_seconds)
time.sleep(random_seconds)

print('Turning on the outlet#%s' % PORT)
switch.on(PORT)

print('The powerstate of the outlet is currently', switch[PORT].state)
print('The current status of the powerswitch is:')
print(switch)
