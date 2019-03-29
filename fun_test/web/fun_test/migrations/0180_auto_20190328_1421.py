# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-03-28 21:21
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0179_auto_20190327_1808'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField()),
                ('job_id', models.IntegerField(unique=True)),
                ('test_bed_type', models.TextField(default=b'', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TeraMarkNfaPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('output_latency', models.IntegerField(default=-1, verbose_name=b'nsecs')),
                ('output_latency_unit', models.TextField(default=b'nsecs')),
                ('output_bandwidth', models.FloatField(default=-1, verbose_name=b'Gbps')),
                ('output_bandwidth_unit', models.TextField(default=b'Gbps')),
            ],
        ),
        migrations.RemoveField(
            model_name='suiteexecution',
            name='catalog_reference',
        ),
        migrations.RemoveField(
            model_name='teramarkdfaperformance',
            name='input_graph_index',
        ),
        migrations.RemoveField(
            model_name='teramarkdfaperformance',
            name='output_matches',
        ),
        migrations.RemoveField(
            model_name='teramarkdfaperformance',
            name='output_processed',
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='build_url',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='dynamic_suite_spec',
            field=models.TextField(default=b'{}', null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='email_on_failure_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='emails',
            field=models.TextField(default=b'[]', null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='environment',
            field=models.TextField(default=b'{}', null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='inputs',
            field=models.TextField(default=b'{}', null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='is_scheduled_job',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='queued_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='repeat_in_minutes',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='requested_days',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='requested_hour',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='requested_minute',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='requested_priority_category',
            field=models.TextField(default=b'normal'),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='scheduling_type',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='state',
            field=models.TextField(default=b'SUBMITTED'),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='timezone_string',
            field=models.TextField(default=b'PST'),
        ),
        migrations.AddField(
            model_name='teramarkdfaperformance',
            name='output_bandwidth_unit',
            field=models.TextField(default=b'Gbps'),
        ),
        migrations.AddField(
            model_name='teramarkdfaperformance',
            name='output_latency_unit',
            field=models.TextField(default=b'nsecs'),
        ),
        migrations.AlterField(
            model_name='suiteexecution',
            name='scheduled_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='suiteexecution',
            name='submitted_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='teramarkdfaperformance',
            name='output_bandwidth',
            field=models.FloatField(default=-1, verbose_name=b'Gbps'),
        ),
        migrations.AlterField(
            model_name='teramarkdfaperformance',
            name='output_latency',
            field=models.IntegerField(default=-1, verbose_name=b'nsecs'),
        ),
    ]
