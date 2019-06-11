import sys
import time
import dlipower

USER = "admin"
PASSWORD = "Precious1*"

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

print('Sleeping for 5 seconds')
time.sleep(5)

print('Turning on the outlet#%s' % PORT)
switch.on(PORT)

print('The powerstate of the outlet is currently', switch[PORT].state)
print('The current status of the powerswitch is:')
print(switch)
