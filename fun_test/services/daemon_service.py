from fun_settings import LOGS_DIR

import logging
import logging.handlers
import sys
import abc
from web.fun_test.django_interactive import *
from web.fun_test.models import Daemon

TEN_MB = 1e7


class Service:
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def service_name(self):
        pass

    def __init__(self, console_log=False):
        self.logger = logging.getLogger("{}_logger".format(self.service_name))
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        log_file_name = "{}/{}_log.txt".format(LOGS_DIR, self.service_name)

        if not console_log:
            handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=TEN_MB, backupCount=5)
        else:
            handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(hdlr=handler)

    @abc.abstractmethod
    def run(self):
        pass

    def get_logger(self):
        return self.logger

    def beat(self):
        daemon = Daemon.get(name=self.service_name)
        daemon.beat()

    def report_exception(self, exception_log):
        daemon = Daemon.get(name=self.service_name)
        daemon.add_exception_log(log=exception_log)

    def service_assert(self, expression, log):
        if not expression:
            self.error(message=expression)
            self.report_exception(exception_log=log)
            raise Exception(log)

    def error(self, message):
        s = "ERROR: {}".format(message)
        self.logger.exception(s)

    def alert(self, message):
        s = "ALERT: {}".format(message)
        self.logger.error(s)

    def info(self, message):
        s = "{}".format(message)
        self.logger.info(s)