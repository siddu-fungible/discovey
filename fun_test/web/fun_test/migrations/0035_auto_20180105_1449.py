# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-01-05 22:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0034_catalogsuiteexecution_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogtestcaseexecution',
            name='bugs',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='catalogtestcaseexecution',
            name='comments',
            field=models.TextField(default=b''),
        ),
    ]
