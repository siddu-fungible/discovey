# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-04 03:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0018_auto_20171203_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogsuite',
            name='name',
            field=models.TextField(default=b'UNKNOWN', unique=True),
        ),
    ]
