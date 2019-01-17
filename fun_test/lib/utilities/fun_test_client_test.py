#!/usr/bin/env python
import json
import os
from fun_test_client import FunTestClient

LOG_FILE = "fun_test_client.log.html"
default_to_addresses = ["john.abraham@fungible.com"]
POLL_INTERVAL = 10
BASE_URL = "http://127.0.0.1:5000"

import threading

def worker(fun_test_client):
    data = {"script_path": "/storage/thin_block_volume_performance.py"}
    fun_test_client._do_post(url="/regression/get_script_history", data=json.dumps(data))
    return



# BASE_URL = "http://qa-ubuntu-01"

if __name__ == "__main__":
    fun_test_client = FunTestClient(base_url=BASE_URL)
    fun_test_client.DEBUG = False
    data = {"script_path": "/networking/qos/test_pir.py"}
    data = {"script_path": "/storage/thin_block_volume_performance.py"}
    from_time = 1541030400 * 1000
    to_time = 1547501328 * 1000
    test_case_execution_tags = ["tagn1"]
    data = {"from_time": from_time,
            "to_time": to_time,
            "module": "networking",
            "test_case_execution_tags": test_case_execution_tags}

    '''threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(fun_test_client, ))
        threads.append(t)
        t.start()'''

    for i in range(1):
        o = fun_test_client._do_post(url="/regression/get_test_case_executions_by_time", data=json.dumps(data))

        for a in o["data"]:
            print a

    h = 0