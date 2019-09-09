# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-09-08 18:53
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0264_auto_20190904_1728'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchedulerConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_unlock_warning_time', models.IntegerField(default=30)),
                ('debug', models.BooleanField(default=False)),
            ],
        ),
        migrations.RenameField(
            model_name='suite',
            old_name='tyoe',
            new_name='type',
        ),
        migrations.AddField(
            model_name='asset',
            name='manual_lock_expiry_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='is_re_run',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='re_run_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True),
        ),
        migrations.AddField(
            model_name='suiteexecution',
            name='suite_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='suiteexecution',
            name='assets_used',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True),
        ),
        migrations.AlterField(
            model_name='suiteexecution',
            name='run_time',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True),
        ),
    ]
