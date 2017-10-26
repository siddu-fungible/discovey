from lib.fun.f1 import DockerF1
import types, json
class ToDictMixin:
    TO_DICT_VARS = []
    def to_dict(self):
        d = {}
        for x in self.TO_DICT_VARS:
            val = getattr(self, x)
            t = type(val)
            if t == types.InstanceType:
                d[x] = val.to_dict()
            elif (t == types.DictionaryType) or (t == types.DictType):
                d2 = {}
                for key in val:
                    d2[key] = self.get_val(val[key])
                d[x] = d2
            elif (t == types.ListType):
                l = []
                for element in val:
                    l.append(self.get_val(element))
                d[x] = l
            elif (str(t).startswith("<class")):
                d[x] = val.to_dict()
            else:
                d[x] = val
        return d

    def get_val(self, val):
        result = val
        t = type(val)
        if t == types.InstanceType:
            result = val.to_dict()
        elif (t == types.DictionaryType) or (t == types.DictType):
            d2 = {}
            for key in val:
                d2[key] = self.get_val(val[key])
            result = d2
        elif (t == types.ListType):
            l = []
            for element in val:
                l.append(self.get_val(element))
            result = l
        elif (str(t).startswith("<class")):
            result = val.to_dict()
        else:
            result = val
        return result

class B(ToDictMixin):
    TO_DICT_VARS = ["name"]
    def __init__(self):
        self.name = "B"


class A(ToDictMixin):
    # TO_DICT_VARS = ["duh", "b", "c"]
    TO_DICT_VARS = [ "d"]

    def __init__(self):
        self.duh = 5
        self.b = B()
        self.c = {"j": 1, "h": B()}
        self.d = ["k",  DockerF1(host_ip="124")]


a = A()

print json.dumps(a.to_dict(), indent=4)

d = DockerF1(host_ip="124")
t = type(d)
s = str(t.__name__)
if type(d) == types.ClassType:
    print "Class"

if type(d) == types.InstanceType:
    print "inst"

if type(d) == types.ObjectType:
    print "obj"


if type(d) == types.DictType:
    print "Dict"

e = a if e else 1
print e