# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-08-28 20:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0258_auto_20190828_0701'),
    ]

    operations = [
        migrations.AddField(
            model_name='testbed',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
    ]