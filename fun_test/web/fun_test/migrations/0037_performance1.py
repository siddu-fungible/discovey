# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-02-01 18:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0036_auto_20180106_0654'),
    ]

    operations = [
        migrations.CreateModel(
            name='Performance1',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=30)),
                ('input1', models.CharField(max_length=30)),
                ('input2', models.IntegerField()),
                ('output1', models.IntegerField()),
                ('output2', models.IntegerField()),
                ('output3', models.CharField(max_length=30)),
            ],
        ),
    ]
