import types
class ToDictMixin:
    TO_DICT_VARS = []
    def to_dict(self):
        d = {}
        for x in self.TO_DICT_VARS:
            if not hasattr(self, x):
                continue
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
