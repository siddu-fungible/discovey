# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-19 20:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='f1',
            name='ip',
            field=models.GenericIPAddressField(default='127.0.0.1'),
        ),
    ]
