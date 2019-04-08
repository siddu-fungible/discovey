# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-11-14 21:06
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0115_auto_20181114_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedulerinfo',
            name='last_restart_request_time',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='schedulerinfo',
            name='last_start_time',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='teramarkcryptoperformance',
            name='input_algorithm',
            field=models.CharField(choices=[(0, b'AES_ECB'), (1, b'AES_GCM'), (2, b'AES_CBC'), (3, b'AES_XTS'), (4, b'SHA_256')], default=b'', max_length=30),
        ),
    ]
