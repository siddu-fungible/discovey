# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2019-12-18 06:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0294_releasecatalogexecution_build_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='releasecatalogexecution',
            name='error_message',
            field=models.TextField(default=None, null=True),
        ),
    ]