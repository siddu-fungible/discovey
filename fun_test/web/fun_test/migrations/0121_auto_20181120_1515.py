# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-11-20 23:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0120_auto_20181120_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teramarklookupengineperformance',
            name='output_lookup_per_sec_avg',
            field=models.IntegerField(default=-1, verbose_name=b'lookups per sec'),
        ),
        migrations.AlterField(
            model_name='teramarklookupengineperformance',
            name='output_lookup_per_sec_max',
            field=models.IntegerField(default=-1, verbose_name=b'lookups per sec'),
        ),
        migrations.AlterField(
            model_name='teramarklookupengineperformance',
            name='output_lookup_per_sec_min',
            field=models.IntegerField(default=-1, verbose_name=b'lookups per sec'),
        ),
    ]
