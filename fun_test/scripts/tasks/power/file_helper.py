from datetime import datetime
import json


def get_file_handle(file_name="wael.txt"):
    f = open(file_name, 'a+')
    return f


def add_data(f, data, extra_line=False, heading="Result"):
    # for data in data_list:
    f.write("\n")
    f.write("-----------------{}------------------".format(heading))
    f.write('\n')
    f.write("Time = {}".format(data["time"]))
    f.write("\n")
    f.write("\n")
    if type(data["dpcsh_output"]) is dict:
        add_json_data(f, data["dpcsh_output"])
    else:
        f.write(data["dpcsh_output"])
    f.write("\n")
    if extra_line:
        f.write("\n")


def add_json_data(f, data):
    json.dump(data, f, indent=4)
    f.write("\n")