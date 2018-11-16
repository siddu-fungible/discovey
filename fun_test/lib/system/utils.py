from lib.system.fun_test import fun_test
import os
import types, collections, json, commentjson
from pathos.multiprocessing import ProcessingPool, cpu_count
import uuid


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


class MultiProcessingTasks:

    def __init__(self):
        self.task_list = []
        self.p_results = {}

    def add_task(self, func, func_args=None, func_kwargs=None, task_key=None):
        self.task_list.append((func, func_args, func_kwargs, task_key))

    @fun_test.safe
    def run(self, max_parallel_processes=cpu_count(), parallel=True):
        p = ProcessingPool(nodes=max_parallel_processes)
        p_func = p.apipe if parallel else p.pipe

        for func_args in self.task_list:
            func, args, kwargs, task_key = func_args
            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}
            result = p_func(func, *args, **kwargs)
            if task_key is None:
                task_key = (func, args, kwargs)
            self.p_results[task_key] = result
        p.close()
        p.clear()
        p.join()

        return True

    def get_result(self, task_key):
        return self.p_results[task_key].get(timeout=1)


def old_parse_file_to_json(file_name):
    result = None
    if os.path.exists(file_name):
        try:
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = json.loads(contents)
        except Exception as ex:
            fun_test.critical("{} has an invalid json format".format(file_name))
    else:
        fun_test.critical("{} path does not exist".format(file_name))
    return result


def parse_file_to_json(file_name):
    result = None
    if os.path.exists(file_name):
        try:
            with open(file_name, "r") as infile:
                result = commentjson.load(infile)
        except Exception as ex:
            fun_test.critical("{} has an invalid json format".format(file_name))
    else:
        fun_test.critical("{} path does not exist".format(file_name))
    return result


def parse_str_to_json(jstr):
    result = None
    if isinstance(jstr, str):
        try:
            result = commentjson.loads(jstr)
        except Exception as ex:
            fun_test.critical("{} has an invalid json format".format(jstr))
    else:
        fun_test.critical("Argument received is not valid Python String")
    return result


def generate_uuid(length=16):
    result = None
    try:
        result = str(uuid.uuid4()).replace("-", "")[length:]
    except Exception as ex:
        fun_test.critical(str(ex))
    return result