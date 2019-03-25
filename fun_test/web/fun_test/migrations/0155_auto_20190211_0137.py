# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-02-11 09:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0154_milestonemarkers'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuiteReRunInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_suite_execution_id', models.IntegerField()),
                ('re_run_suite_execution_id', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='suite_type',
            field=models.TextField(default=b'regular'),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='test_bed_type',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='testcaseexecution',
            name='re_run_history',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='testcaseexecution',
            name='re_run_state',
            field=models.TextField(default=b''),
        ),
    ]
