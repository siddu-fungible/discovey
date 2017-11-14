from fun_settings import WEB_SERVER_PORT
from fun_global import is_regression_server
import socket

def get_homepage_url():
    hostname = "localhost"
    if is_regression_server():
        hostname = socket.gethostname()
    s = "http://{}:{}".format(hostname, WEB_SERVER_PORT)
    return s

def get_regression_url():
    return get_homepage_url() + "/regression"

def get_suite_detail_url(suite_execution_id):
    return "{}/suite_detail/{}".format(get_regression_url(), suite_execution_id)

