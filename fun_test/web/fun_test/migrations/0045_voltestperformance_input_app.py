# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-06-26 00:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0044_auto_20180625_1359'),
    ]

    operations = [
        migrations.AddField(
            model_name='voltestperformance',
            name='input_app',
            field=models.CharField(choices=[(0, b'voltest')], default=b'voltest', max_length=20),
        ),
    ]
