# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-02-14 22:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0003_auto_20180214_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volumeperformance',
            name='input_size',
            field=models.TextField(verbose_name=b'Data size'),
        ),
    ]
