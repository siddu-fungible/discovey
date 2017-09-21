# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class F1(models.Model):
    ip = models.GenericIPAddressField(default="127.0.0.1")
    name = models.CharField(max_length=100, default="unknown")

    def __str__(self):
        return "{}-{}".format(self.ip, self.name)

class Tg(models.Model):
    ip = models.GenericIPAddressField(default="127.0.0.1")
    name = models.CharField(max_length=100, default="unknown")

    def __str__(self):
        return "{}-{}".format(self.ip, self.name)


class Session(models.Model):
    session_id = models.IntegerField(unique=True, default=10)

    def __str__(self):
        return "{}".format(self.session_id)
