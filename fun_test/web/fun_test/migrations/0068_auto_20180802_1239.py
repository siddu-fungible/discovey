# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-08-02 19:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0067_wudispatchtestperformance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wudispatchtestperformance',
            name='input_app',
            field=models.CharField(choices=[(0, b'dispatch_speed_test')], default=b'dispatch_speed_test', max_length=30),
        ),
        migrations.AlterField(
            model_name='wudispatchtestperformance',
            name='input_metric_name',
            field=models.CharField(choices=[(0, b'wu_dispatch_latency_cycles')], max_length=30, verbose_name=b'Input metric name'),
        ),
    ]
