# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-02-05 22:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0052_modelmapping'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelmapping',
            name='model_name',
            field=models.TextField(default=b'Performance1'),
        ),
    ]
