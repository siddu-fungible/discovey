# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-04-01 22:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0178_auto_20190327_1046'),
    ]

    operations = [
        migrations.AddField(
            model_name='triage',
            name='email',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='triage',
            name='fun_os_make_flags',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='triageflow',
            name='email',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='triageflow',
            name='fun_os_make_flags',
            field=models.TextField(default=b''),
        ),
    ]
