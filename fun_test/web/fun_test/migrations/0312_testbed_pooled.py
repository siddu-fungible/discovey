# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2020-02-21 20:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0311_rawvolumenvmetcpmultihostperformance_input_shared_volume'),
    ]

    operations = [
        migrations.AddField(
            model_name='testbed',
            name='pooled',
            field=models.BooleanField(default=False),
        ),
    ]
