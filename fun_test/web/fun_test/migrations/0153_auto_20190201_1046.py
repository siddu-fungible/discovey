# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-02-01 18:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0152_auto_20190131_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teramarkcryptoperformance',
            name='output_throughput',
            field=models.FloatField(default=-1, verbose_name=b'Gbps'),
        ),
        migrations.AlterField(
            model_name='teramarkzipdeflateperformance',
            name='output_bandwidth_avg',
            field=models.FloatField(default=-1, verbose_name=b'Gbps'),
        ),
        migrations.AlterField(
            model_name='teramarkziplzmaperformance',
            name='output_bandwidth_avg',
            field=models.FloatField(default=-1, verbose_name=b'Gbps'),
        ),
    ]
