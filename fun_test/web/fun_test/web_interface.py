from fun_settings import WEB_SERVER_PORT, REGRESSION_SERVER_DOMAIN_NAME
from fun_global import is_lite_mode, is_production_mode
import socket


def get_homepage_url():
    hostname = "localhost"
    try:
        hostname = socket.gethostname()
    except Exception as ex:
        print (str(ex))
    if not is_lite_mode():
        hostname = socket.gethostname()

    s = "http://{}:{}".format(hostname, WEB_SERVER_PORT)
    if is_production_mode():
        s = "http://{}".format(REGRESSION_SERVER_DOMAIN_NAME)

    return s


def get_regression_url():
    return get_homepage_url() + "/regression"


def get_suite_detail_url(suite_execution_id):
    return "{}/suite_detail/{}".format(get_regression_url(), suite_execution_id)

