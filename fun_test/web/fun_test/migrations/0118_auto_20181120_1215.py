# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-11-20 20:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0117_auto_20181116_1137'),
    ]

    operations = [
        migrations.RenameField(
            model_name='regresssionscripts',
            old_name='module',
            new_name='modules',
        ),
    ]
