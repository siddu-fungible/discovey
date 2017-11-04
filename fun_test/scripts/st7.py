import collections
class A:
    def __init__(self):
        self.a = 5
        self.b = 6


d1 = {"a": 1, "c": [1, 2], "b": A()}
d2 = {"c": [1, 2], "a": 1, "b": A()}


od1 = collections.OrderedDict()
od2 = collections.OrderedDict()

sorted_keys = sorted(d1.keys())
for k in sorted_keys:
    od1[k] = d1[k]
    od2[k] = d1[k]

a1 = A()
a2 = A()
print a1 == a2
print d1 == d2