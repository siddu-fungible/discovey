# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-07-02 22:55
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0231_auto_20190627_2030'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlibabaPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_volume_type', models.TextField(verbose_name=b'Volume type')),
                ('input_test', models.TextField(verbose_name=b'Test type')),
                ('input_block_size', models.TextField(verbose_name=b'Block size')),
                ('input_io_depth', models.IntegerField(verbose_name=b'IO depth')),
                ('input_io_size', models.TextField(verbose_name=b'IO size')),
                ('input_operation', models.TextField(verbose_name=b'Operation type')),
                ('input_num_ssd', models.IntegerField(verbose_name=b'Number of SSD(s)')),
                ('input_num_volume', models.IntegerField(verbose_name=b'Number of volume(s)')),
                ('input_num_threads', models.IntegerField(verbose_name=b'Threads')),
                ('input_platform', models.TextField(default=b'F1')),
                ('input_version', models.CharField(default=b'', max_length=50, verbose_name=b'Version')),
                ('output_write_iops', models.IntegerField(default=-1, verbose_name=b'Write IOPS')),
                ('output_read_iops', models.IntegerField(default=-1, verbose_name=b'Read IOPS')),
                ('output_write_throughput', models.FloatField(default=-1, verbose_name=b'Write throughput')),
                ('output_read_throughput', models.FloatField(default=-1, verbose_name=b'Read throughput')),
                ('output_write_avg_latency', models.IntegerField(default=-1, verbose_name=b'Write avg latency')),
                ('output_write_90_latency', models.IntegerField(default=-1, verbose_name=b'Write 90% latency')),
                ('output_write_95_latency', models.IntegerField(default=-1, verbose_name=b'Write 95% latency')),
                ('output_write_99_99_latency', models.IntegerField(default=-1, verbose_name=b'Write 99.99% latency')),
                ('output_write_99_latency', models.IntegerField(default=-1, verbose_name=b'Write 99% latency')),
                ('output_read_avg_latency', models.IntegerField(default=-1, verbose_name=b'Read avg latency')),
                ('output_read_90_latency', models.IntegerField(default=-1, verbose_name=b'Read 90% latency')),
                ('output_read_95_latency', models.IntegerField(default=-1, verbose_name=b'Read 95% latency')),
                ('output_read_99_99_latency', models.IntegerField(default=-1, verbose_name=b'Read 99.99% latency')),
                ('output_read_99_latency', models.IntegerField(default=-1, verbose_name=b'Read 99% latency')),
                ('output_write_iops_unit', models.TextField(default=b'ops')),
                ('output_read_iops_unit', models.TextField(default=b'ops')),
                ('output_write_throughput_unit', models.TextField(default=b'Mbps')),
                ('output_read_throughput_unit', models.TextField(default=b'Mbps')),
                ('output_write_avg_latency_unit', models.TextField(default=b'usecs')),
                ('output_write_90_latency_unit', models.TextField(default=b'usecs')),
                ('output_write_95_latency_unit', models.TextField(default=b'usecs')),
                ('output_write_99_99_latency_unit', models.TextField(default=b'usecs')),
                ('output_write_99_latency_unit', models.TextField(default=b'usecs')),
                ('output_read_avg_latency_unit', models.TextField(default=b'usecs')),
                ('output_read_90_latency_unit', models.TextField(default=b'usecs')),
                ('output_read_95_latency_unit', models.TextField(default=b'usecs')),
                ('output_read_99_99_latency_unit', models.TextField(default=b'usecs')),
                ('output_read_99_latency_unit', models.TextField(default=b'usecs')),
            ],
        ),
    ]