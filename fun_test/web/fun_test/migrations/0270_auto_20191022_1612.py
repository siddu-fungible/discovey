# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-10-22 23:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0269_rdsclientperformance'),
    ]

    operations = [
        migrations.AddField(
            model_name='performanceuserworkspaces',
            name='alert_emails',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='performanceuserworkspaces',
            name='subscribe_to_alerts',
            field=models.BooleanField(default=False),
        ),
    ]
