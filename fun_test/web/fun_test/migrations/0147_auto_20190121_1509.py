# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-01-21 23:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0146_scriptinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nutransitperformance',
            name='interpolation_allowed',
            field=models.BooleanField(default=False),
        ),
    ]
