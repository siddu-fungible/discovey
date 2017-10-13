# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-13 20:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0008_traffictask_logs'),
    ]

    operations = [
        migrations.CreateModel(
            name='IkvVideoTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.IntegerField(default=10, unique=True)),
                ('status', models.CharField(default=b'NOT_RUN', max_length=15)),
                ('logs', models.CharField(default='', max_length=2048)),
            ],
        ),
    ]
