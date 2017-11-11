from fun_settings import WEB_SERVER_PORT
def get_homepage_url():
    hostname = "server17"
    s = "http://{}:{}".format(WEB_SERVER_PORT, hostname)
    return s

def get_regression_url():
    return get_homepage_url() + "/regression"

def get_suite_detail_url(suite_execution_id):
    return "{}/suite_detail/{}".format(get_regression_url(), suite_execution_id)

