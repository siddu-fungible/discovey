# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-11-21 17:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0120_auto_20181120_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='regresssionscripts',
            name='components',
            field=models.TextField(default=b"['component1']"),
        ),
        migrations.AddField(
            model_name='regresssionscripts',
            name='tags',
            field=models.TextField(default=b"['tag1']"),
        ),
    ]
