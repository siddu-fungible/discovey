# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-17 05:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0026_auto_20171216_2123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogsuiteexecution',
            name='instance_name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
