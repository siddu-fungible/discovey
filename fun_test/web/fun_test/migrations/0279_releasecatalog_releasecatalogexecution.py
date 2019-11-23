# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-11-19 22:26
from __future__ import unicode_literals

import datetime
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0278_auto_20191108_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseCatalog',
            fields=[
                ('funmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fun_test.FunModel')),
                ('name', models.TextField(default=b'TBD')),
                ('description', models.TextField(default=b'TBD')),
                ('created_date', models.DateTimeField(default=datetime.datetime.now)),
                ('modified_date', models.DateTimeField(default=datetime.datetime.now)),
                ('suites', django.contrib.postgres.fields.jsonb.JSONField(default=[])),
            ],
            bases=('fun_test.funmodel',),
        ),
        migrations.CreateModel(
            name='ReleaseCatalogExecution',
            fields=[
                ('funmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='fun_test.FunModel')),
                ('release_catalog_id', models.IntegerField()),
                ('created_date', models.DateTimeField(default=datetime.datetime.now)),
                ('started_date', models.DateTimeField(default=datetime.datetime.now)),
                ('completion_date', models.DateTimeField(default=None, null=True)),
                ('owner', models.EmailField(blank=True, max_length=254, null=True)),
                ('state', models.IntegerField(default=-40)),
            ],
            bases=('fun_test.funmodel',),
        ),
    ]