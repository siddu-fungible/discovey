import re

s = "sda2"

m = re.search(r'[A-Za-z0-9\-]*', s)
if m:
    print m.group(0)