# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-01-25 00:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0148_regresssionscripts_baseline_suite_execution_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='regresssionscripts',
            name='baseline_suite_execution_id',
            field=models.IntegerField(default=-1, null=True),
        ),
    ]
