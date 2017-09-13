# import django
import os
# import fun_test

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()

from django.db import models
from fun_global import RESULTS

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]

class SuiteExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    suite_path = models.CharField(max_length=100)
    submitted_time = models.DateTimeField()
    scheduled_time = models.DateTimeField()
    completed_time = models.DateTimeField()
    test_case_execution_ids = models.CharField(max_length=10000, default="[]")

    def __str__(self):
        s = "Suite: {} {}".format(self.execution_id, self.suite_path)
        return s


class LastSuiteExecution(models.Model):
    last_suite_execution_id = models.IntegerField(unique=True, default=10)


class LastTestCaseExecution(models.Model):
    last_test_case_execution_id = models.IntegerField(unique=True, default=10)

class TestCaseExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    test_case_id = models.IntegerField()
    suite_execution_id = models.IntegerField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="NOTRUN")

    def __str__(self):
        s = "E: {} S: {} T: {} R: {}".format(self.execution_id, self.suite_execution_id,
                                             self.test_case_id, self.result)
        return s


if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass