# Suite ==> JQLs
# ... cache TCs
# ... Delete
# ... set topology
# ... Selected


# Tc

from django.db import models
from web.fun_test.tcm_common import CATALOG_CATEGORIES
from django.core import serializers


class CatalogTestCase(models.Model):
    jira_id = models.IntegerField()

    def __str__(self):
        return str(self.jira_id)

class CatalogSuite(models.Model):
    category = models.CharField(max_length=20,
                                choices=[(k, v) for k, v in CATALOG_CATEGORIES.items()], default=CATALOG_CATEGORIES["ON_DEMAND"])
    jqls = models.TextField(default="[]")
    name = models.TextField(default="UNKNOWN", unique=True)
    test_cases = models.ManyToManyField(CatalogTestCase, blank=True)

    def __str__(self):
        s = "{} {}".format(self.category, self.name)
        return s

