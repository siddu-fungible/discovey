# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-03-13 01:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0008_jenkinsjobidmap'),
    ]

    operations = [
        migrations.AddField(
            model_name='jenkinsjobidmap',
            name='git_commit',
            field=models.TextField(default=b''),
        ),
    ]
