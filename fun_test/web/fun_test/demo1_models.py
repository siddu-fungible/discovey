# import django
import os
# import fun_test

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()
from fun_settings import COMMON_WEB_LOGGER_NAME
from django.db import models
from fun_global import RESULTS
from rest_framework.serializers import ModelSerializer
from datetime import datetime
import logging

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]


class LastBgExecution(models.Model):
    last_bg_execution_id = models.IntegerField(unique=True, default=10)

class BgExecutionStatus(models.Model):
    execution_id = models.IntegerField(unique=True)
    status = models.TextField(choices=RESULT_CHOICES, default=RESULTS["SCHEDULED"])
    output = models.TextField(default="")

    def __str__(self):
        s = "{} {} {}".format(self.execution_id, self.status, self.output)
        return s

if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass
