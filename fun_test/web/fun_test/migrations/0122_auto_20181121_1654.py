# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-11-22 00:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0121_auto_20181121_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='regresssionscripts',
            name='components',
            field=models.TextField(default=b'["component1"]'),
        ),
        migrations.AlterField(
            model_name='regresssionscripts',
            name='tags',
            field=models.TextField(default=b'["tag1"]'),
        ),
    ]
