# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-01-10 22:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0140_suiteexecution_banner'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcaseexecution',
            name='log_prefix',
            field=models.TextField(default=b''),
        ),
    ]
