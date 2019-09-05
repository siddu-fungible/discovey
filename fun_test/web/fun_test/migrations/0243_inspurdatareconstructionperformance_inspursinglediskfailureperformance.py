# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-07-23 22:10
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0242_auto_20190721_1923'),
    ]

    operations = [
        migrations.CreateModel(
            name='InspurDataReconstructionPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_platform', models.TextField(default=b'F1')),
                ('input_version', models.CharField(default=b'', max_length=50, verbose_name=b'Version')),
                ('input_num_hosts', models.IntegerField(default=-1, verbose_name=b'Number of hosts')),
                ('input_block_size', models.TextField(default=b'', verbose_name=b'Block size')),
                ('input_io_depth', models.IntegerField(default=-1, verbose_name=b'IO depth')),
                ('input_size', models.TextField(default=b'', verbose_name=b'Input size')),
                ('input_operation', models.TextField(default=b'', verbose_name=b'Operation type')),
                ('input_fio_job_name', models.TextField(default=b'', verbose_name=b'Input FIO job name')),
                ('output_write_iops', models.IntegerField(default=-1, verbose_name=b'Write IOPS')),
                ('output_read_iops', models.IntegerField(default=-1, verbose_name=b'Read IOPS')),
                ('output_write_throughput', models.FloatField(default=-1, verbose_name=b'Write throughput')),
                ('output_read_throughput', models.FloatField(default=-1, verbose_name=b'Read throughput')),
                ('output_write_avg_latency', models.IntegerField(default=-1, verbose_name=b'Write avg latency')),
                ('output_write_90_latency', models.IntegerField(default=-1, verbose_name=b'Write 90% latency')),
                ('output_write_95_latency', models.IntegerField(default=-1, verbose_name=b'Write 95% latency')),
                ('output_write_99_latency', models.IntegerField(default=-1, verbose_name=b'Write 99% latency')),
                ('output_write_99_99_latency', models.IntegerField(default=-1, verbose_name=b'Write 99.99% latency')),
                ('output_read_avg_latency', models.IntegerField(default=-1, verbose_name=b'Read avg latency')),
                ('output_read_90_latency', models.IntegerField(default=-1, verbose_name=b'Read 90% latency')),
                ('output_read_95_latency', models.IntegerField(default=-1, verbose_name=b'Read 95% latency')),
                ('output_read_99_latency', models.IntegerField(default=-1, verbose_name=b'Read 99% latency')),
                ('output_read_99_99_latency', models.IntegerField(default=-1, verbose_name=b'Read 99.99% latency')),
                ('output_plex_rebuild_time', models.IntegerField(default=-1, verbose_name=b'Plex rebuild time')),
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
                ('output_plex_rebuild_time_unit', models.TextField(default=b'secs')),
            ],
        ),
        migrations.CreateModel(
            name='InspurSingleDiskFailurePerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_platform', models.TextField(default=b'F1')),
                ('input_version', models.CharField(default=b'', max_length=50, verbose_name=b'Version')),
                ('input_num_hosts', models.IntegerField(default=-1, verbose_name=b'Number of hosts')),
                ('input_num_f1s', models.IntegerField(default=1, verbose_name=b"Number of F1's")),
                ('input_volume_size', models.IntegerField(default=-1, verbose_name=b'Volume size')),
                ('input_test_file_size', models.IntegerField(default=-1, verbose_name=b'Test file size')),
                ('input_job_name', models.CharField(default=b'', max_length=50, verbose_name=b'Job name')),
                ('output_base_file_copy_time', models.FloatField(default=-1, verbose_name=b'Base file copy time (sec)')),
                ('output_copy_time_during_plex_fail', models.FloatField(default=-1, verbose_name=b'File copy time during plex fail(sec)')),
                ('output_file_copy_time_during_rebuild', models.FloatField(default=-1, verbose_name=b'File copy time during rebuild (sec)')),
                ('output_plex_rebuild_time', models.FloatField(default=-1, verbose_name=b'Plex rebuild time (sec)')),
                ('output_base_file_copy_time_unit', models.TextField(default=b'secs')),
                ('output_copy_time_during_plex_fail_unit', models.TextField(default=b'secs')),
                ('output_file_copy_time_during_rebuild_unit', models.TextField(default=b'secs')),
                ('output_plex_rebuild_time_unit', models.TextField(default=b'secs')),
            ],
        ),
    ]
