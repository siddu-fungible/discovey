# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-05-28 21:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0220_testcaseinfo_steps'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspurzipcompressionratiosperformance',
            name='input_platform',
            field=models.TextField(default=b'F1'),
        ),
    ]
