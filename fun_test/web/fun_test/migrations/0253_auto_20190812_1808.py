# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-08-13 01:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0252_triage3trial_integration_job_id'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LastTriageFlowId',
            new_name='LastTrialId',
        ),
        migrations.AddField(
            model_name='triage3trial',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='triage3trial',
            name='original_id',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='triage3trial',
            name='reruns',
            field=models.BooleanField(default=False),
        ),
    ]