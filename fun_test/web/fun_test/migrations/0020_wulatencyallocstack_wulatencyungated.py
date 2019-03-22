# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-25 22:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0019_jiracache'),
    ]

    operations = [
        migrations.CreateModel(
            name='WuLatencyAllocStack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=30, verbose_name=b'Software date')),
                ('input_app', models.TextField(choices=[(0, b'wu_latency_test')], default=b'wu_latency_test', verbose_name=b'wu_latency_test: alloc_stack')),
                ('output_min', models.IntegerField(verbose_name=b'Min (ns)')),
                ('output_max', models.IntegerField(verbose_name=b'Max (ns)')),
                ('output_avg', models.IntegerField(verbose_name=b'Avg (ns)')),
            ],
        ),
        migrations.CreateModel(
            name='WuLatencyUngated',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=30, verbose_name=b'Software date')),
                ('input_app', models.TextField(choices=[(0, b'wu_latency_test')], default=b'wu_latency_test', verbose_name=b'wu_latency_test: Ungated WU')),
                ('output_min', models.IntegerField(verbose_name=b'Min (ns)')),
                ('output_max', models.IntegerField(verbose_name=b'Max (ns)')),
                ('output_avg', models.IntegerField(verbose_name=b'Avg (ns)')),
            ],
        ),
    ]
