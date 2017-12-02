# Suite ==> JQLs
# ... cache TCs
# ... Delete
# ... set topology
# ... Selected


# Tc

from django.db import models

class CatalogTestCase(models.Model):
    jira_id = models.IntegerField()

class CatalogSuite(models.Model):
    jqls = models.TextField(default="[]")
    test_cases = models.ManyToManyField(CatalogTestCase)