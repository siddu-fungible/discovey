# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-04-26 23:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0196_jenkinsjobidmap_sdk_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='teramarkjunipernetworkingperformance',
            name='input_half_load_latency',
            field=models.BooleanField(default=False),
        ),
    ]
