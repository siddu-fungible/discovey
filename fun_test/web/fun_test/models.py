# import django
import os
# import fun_test

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()

from django.db import models
from fun_global import RESULTS

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]

TAG_LENGTH = 50

class SuiteExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    suite_path = models.CharField(max_length=100)
    submitted_time = models.DateTimeField()
    scheduled_time = models.DateTimeField()
    completed_time = models.DateTimeField()
    test_case_execution_ids = models.CharField(max_length=10000, default="[]")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="UNKNOWN")  # Currently used to track KILLED entries could be used to cache overall suite result
    version = models.CharField(max_length=50, default="UNKNOWN")
    tags = models.TextField(default="[]")

    def __str__(self):
        s = "Suite: {} {}".format(self.execution_id, self.suite_path)
        return s


class LastSuiteExecution(models.Model):
    last_suite_execution_id = models.IntegerField(unique=True, default=10)


class LastTestCaseExecution(models.Model):
    last_test_case_execution_id = models.IntegerField(unique=True, default=10)

class TestCaseExecution(models.Model):
    script_path = models.CharField(max_length=128)
    execution_id = models.IntegerField(unique=True)
    test_case_id = models.IntegerField()
    suite_execution_id = models.IntegerField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="NOTRUN")
    started_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)


    def __str__(self):
        s = "E: {} S: {} T: {} R: {} P: {}".format(self.execution_id,
                                                   self.suite_execution_id,
                                                   self.test_case_id,
                                                   self.result,
                                                   self.script_path)
        return s


class Tag(models.Model):
    tag = models.CharField(max_length=TAG_LENGTH)

    def __str__(self):
        return self.tag


if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass