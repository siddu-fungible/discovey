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



if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass
