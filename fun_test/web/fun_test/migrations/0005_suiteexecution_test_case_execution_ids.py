# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-11 19:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0004_auto_20170911_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='suiteexecution',
            name='test_case_execution_ids',
            field=models.CharField(default=b'[]', max_length=10000),
        ),
    ]
