# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-08-09 18:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0080_remove_hurawvolumeperformance_input_threads'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hurawvolumeperformance',
            name='input_testbed',
            field=models.CharField(choices=[(0, b'storage1'), (1.0, b'storage2'), (2.0, b'storagenw')], default=b'storage1', max_length=30, verbose_name=b'Testbed'),
        ),
    ]
