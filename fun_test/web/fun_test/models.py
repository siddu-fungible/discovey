# import django
import os
# import fun_test

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()

from django.db import models
from fun_global import RESULTS
from web.fun_test.jira_models import *
from web.fun_test.metrics_models import *

from web.fun_test.site_state import site_state

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]

TAG_LENGTH = 50

class CatalogTestCase(models.Model):
    jira_id = models.IntegerField()

    def __str__(self):
        return str(self.jira_id)

class TestBed(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} {}".format(self.name, self.description)


class CatalogSuite(models.Model):
    category = models.CharField(max_length=20,
                                choices=[(k, v) for k, v in CATALOG_CATEGORIES.items()],
                                default=CATALOG_CATEGORIES["ON_DEMAND"])
    jqls = models.TextField(default="[]")
    name = models.TextField(default="UNKNOWN", unique=True)
    test_cases = models.ManyToManyField(CatalogTestCase, blank=True)


    def __str__(self):
        s = "{} {}".format(self.category, self.name)
        return s

class SuiteExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    suite_path = models.CharField(max_length=100)
    submitted_time = models.DateTimeField()
    scheduled_time = models.DateTimeField()
    completed_time = models.DateTimeField()
    test_case_execution_ids = models.CharField(max_length=10000, default="[]")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="UNKNOWN")
    tags = models.TextField(default="[]")
    version = models.CharField(max_length=50, default="UNKNOWN")
    catalog_reference = models.TextField(null=True, blank=True, default=None)

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
    overridden_result = models.BooleanField(default=False)
    bugs = models.TextField(default="[]")
    comments = models.TextField(default="")

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

class Engineer(models.Model):
    email = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)

    def __str__(self):
        return "{} {}".format(self.short_name, self.email)



class CatalogSuiteExecution(models.Model):
    suite_execution_id = models.IntegerField(unique=True)
    owner_email = models.EmailField()
    instance_name = models.CharField(max_length=50, unique=True)
    catalog_name = models.TextField(default="UNKNOWN")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="UNKNOWN")
    active = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {} {}".format(self.suite_execution_id, self.owner_email, self.instance_name, self.result)

class CatalogTestCaseExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    catalog_suite_execution_id = models.IntegerField(default=0)
    jira_id = models.IntegerField()
    engineer = models.ForeignKey(Engineer)
    test_bed = models.CharField(max_length=100, default="simulation")

    # result

    def __str__(self):
        return "{} {} {} {}".format(self.execution_id, self.jira_id, self.engineer, self.test_bed)


if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass
