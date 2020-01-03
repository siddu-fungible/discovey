from lib.utilities.fun_test_client import FunTestClient
base_url = "http://0.0.0.0:5000"
from datetime import datetime
# base_url = "http://server17:5000"
# base_url = "http://integration.fungible.local"

fun_test_client = FunTestClient(base_url=base_url)
fun_test_client.DEBUG = True
start = datetime.now()
fun_test_client._do_get(url='/api/v1/regression/test_beds')
stop = datetime.now()

print "Time taken: {}".format((stop - start).total_seconds())