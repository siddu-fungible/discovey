from fun_settings import WEB_SERVER_PORT, REGRESSION_SERVER_DOMAIN_NAME
from fun_global import is_lite_mode, is_production_mode, Codes
import socket
from web.fun_test.models import SiteConfig


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


def get_regression_server_url():
    return "http://{}".format(REGRESSION_SERVER_DOMAIN_NAME)

def get_regression_url():
    return get_homepage_url() + "/regression"

def get_performance_url():
    return get_homepage_url() + "/performance"


def get_suite_detail_url(suite_execution_id):
    return "{}/suite_detail/{}".format(get_regression_url(), suite_execution_id)

def set_annoucement(announcement):
    if not SiteConfig.objects.count():
        SiteConfig().save()

    site_config = SiteConfig.objects.first()
    site_config.announcement = announcement
    site_config.save()

def clear_announcements():
    if SiteConfig.objects.count():
        site_config = SiteConfig.objects.first()
        site_config.announcement = ""
        site_config.save()



