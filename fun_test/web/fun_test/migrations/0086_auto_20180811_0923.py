# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-08-11 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0085_timekeeper_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='timekeeper',
            old_name='last_analytics_db_status_update',
            new_name='time',
        ),
        migrations.AlterField(
            model_name='timekeeper',
            name='name',
            field=models.TextField(default=b'', unique=True),
        ),
    ]
