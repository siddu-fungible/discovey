import types, collections
class ToDictMixin:
    TO_DICT_VARS = []

    def to_dict(self):
        d = {}
        for x in self.TO_DICT_VARS:
            if not hasattr(self, x):
                continue
            val = getattr(self, x)
            d[x] = self.get_val(val)
        return d

    def get_val(self, val):
        result = val
        t = type(val)
        if t == types.InstanceType:
            result = val.to_dict()
        elif (t == types.DictionaryType) or (t == types.DictType) or (isinstance(val, collections.OrderedDict)):
            d2 = {}
            for key in val:
                d2[key] = self.get_val(val[key])
            result = d2
        elif (t == types.ListType) or (isinstance(val, set)):
            l = []
            for element in val:
                l.append(self.get_val(element))
            result = l
        elif (str(t).startswith("<class")):
            result = val.to_dict()
        else:
            result = val
        return result
