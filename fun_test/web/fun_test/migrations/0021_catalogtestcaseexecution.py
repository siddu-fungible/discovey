# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-14 19:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0020_engineer'),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogTestCaseExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('execution_id', models.IntegerField(unique=True)),
                ('jira_id', models.IntegerField()),
                ('engineer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fun_test.Engineer')),
            ],
        ),
    ]
