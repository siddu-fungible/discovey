# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-05-12 03:01
from __future__ import unicode_literals

import datetime
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0206_auto_20190510_1652'),
    ]

    operations = [
        migrations.CreateModel(
            name='Triage2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_id', models.IntegerField()),
                ('triage_id', models.IntegerField()),
                ('triage_type', models.CharField(default=b'SCORES', max_length=15)),
                ('from_fun_os_sha', models.TextField()),
                ('to_fun_os_sha', models.TextField()),
                ('submission_date_time', models.DateTimeField(default=datetime.datetime.now)),
                ('status', models.TextField(default=-100)),
                ('result', models.TextField(default=b'UNKNOWN')),
                ('build_parameters', django.contrib.postgres.fields.jsonb.JSONField()),
                ('current_trial_set_id', models.IntegerField(default=-1)),
                ('current_trial_set_count', models.IntegerField(default=-1)),
            ],
        ),
        migrations.CreateModel(
            name='Triage2Trial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('triage_id', models.IntegerField()),
                ('fun_os_sha', models.TextField()),
                ('trial_set_id', models.IntegerField(default=-1)),
                ('status', models.IntegerField(default=-100)),
            ],
        ),
    ]
