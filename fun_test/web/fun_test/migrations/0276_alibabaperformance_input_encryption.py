# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-11-07 23:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0275_cryptofastpathperformance'),
    ]

    operations = [
        migrations.AddField(
            model_name='alibabaperformance',
            name='input_encryption',
            field=models.BooleanField(default=False),
        ),
    ]