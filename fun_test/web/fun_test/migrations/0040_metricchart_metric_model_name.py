# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-02-03 18:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0039_auto_20180203_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricchart',
            name='metric_model_name',
            field=models.TextField(default=b'Performance1'),
        ),
    ]
