# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-04-24 20:55
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0194_jenkinsjobidmap_lsf_job_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeraMarkFunTcpThroughputPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('interpolated', models.BooleanField(default=False)),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_frame_size', models.FloatField(verbose_name=b'Frame Size')),
                ('input_mode', models.CharField(default=b'', max_length=20, verbose_name=b'Port modes')),
                ('input_version', models.CharField(max_length=50, verbose_name=b'Version')),
                ('input_flow_type', models.CharField(default=b'', max_length=50, verbose_name=b'Flow Type')),
                ('input_num_flows', models.IntegerField(default=1, verbose_name=b'Number of flows')),
                ('output_throughput', models.FloatField(verbose_name=b'Throughput in Gbps')),
                ('output_pps', models.FloatField(verbose_name=b'Packets per sec')),
                ('output_throughput_unit', models.TextField(default=b'Gbps')),
                ('output_pps_unit', models.TextField(default=b'Mpps')),
            ],
        ),
    ]