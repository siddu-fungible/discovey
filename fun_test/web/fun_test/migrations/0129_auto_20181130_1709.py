# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-12-01 01:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0128_auto_20181129_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_boot_success_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'Boot success'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_eeprom_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'EEPROM Loading'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_firmware_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'Firmware'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_flash_type_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'Flash type detection'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_host_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'Host BOOT'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_main_loop_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'Main Loop'),
        ),
        migrations.AlterField(
            model_name='boottimeperformance',
            name='output_sbus_boot_time',
            field=models.FloatField(default=-1, verbose_name=b'SBUS Loading'),
        ),
    ]
