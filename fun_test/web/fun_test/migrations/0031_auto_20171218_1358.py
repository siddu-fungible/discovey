# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-18 21:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0030_catalogsuite_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='catalogsuite',
            name='result',
        ),
        migrations.AddField(
            model_name='catalogsuiteexecution',
            name='result',
            field=models.CharField(choices=[(b'SCHEDULED', b'SCHEDULED'), (b'FAILED', b'FAILED'), (b'SKIPPED', b'SKIPPED'), (b'ABORTED', b'ABORTED'), (b'PASSED', b'PASSED'), (b'UNKNOWN', b'UNKNOWN'), (b'IN_PROGRESS', b'IN_PROGRESS'), (b'KILLED', b'KILLED'), (b'NOT_RUN', b'NOT_RUN'), (b'QUEUED', b'QUEUED')], default=b'UNKNOWN', max_length=10),
        ),
    ]
