# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-05-14 17:59
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0030_ecperformance'),
    ]

    operations = [
        migrations.AddField(
            model_name='unittestperformance',
            name='input_job_id',
            field=models.IntegerField(default=0, verbose_name=b'Job Id'),
        ),
        migrations.AlterField(
            model_name='allocspeedperformance',
            name='input_date_time',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date'),
        ),
        migrations.AlterField(
            model_name='ecperformance',
            name='input_date_time',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date'),
        ),
        migrations.AlterField(
            model_name='unittestperformance',
            name='input_date_time',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date'),
        ),
        migrations.AlterField(
            model_name='wulatencyallocstack',
            name='input_date_time',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date'),
        ),
        migrations.AlterField(
            model_name='wulatencyungated',
            name='input_date_time',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date'),
        ),
    ]
