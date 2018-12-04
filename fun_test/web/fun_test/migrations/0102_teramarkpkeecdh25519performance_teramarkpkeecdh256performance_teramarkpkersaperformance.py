# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-10-23 20:36
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fun_test', '0101_bgexecutionstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeraMarkPkeEcdh25519Performance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_app', models.CharField(choices=[(0, b'pke_ecdh_soak_25519')], default=b'pke_ecdh_soak_25519', max_length=30)),
                ('input_metric_name', models.CharField(choices=[(0, b'ECDH_25519')], default=b'ECDH_25519', max_length=40)),
                ('output_ops_per_sec', models.IntegerField(default=-1, verbose_name=b'ops per sec')),
            ],
        ),
        migrations.CreateModel(
            name='TeraMarkPkeEcdh256Performance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_app', models.CharField(choices=[(0, b'pke_ecdh_soak_256')], default=b'pke_ecdh_soak_256', max_length=30)),
                ('input_metric_name', models.CharField(choices=[(0, b'ECDH_P256')], default=b'ECDH_P256', max_length=40)),
                ('output_ops_per_sec', models.IntegerField(default=-1, verbose_name=b'ops per sec')),
            ],
        ),
        migrations.CreateModel(
            name='TeraMarkPkeRsaPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interpolation_allowed', models.BooleanField(default=False)),
                ('interpolated', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'PASSED', max_length=30, verbose_name=b'Status')),
                ('input_date_time', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'Date')),
                ('input_app', models.CharField(choices=[(0, b'pke_rsa_crt_dec_no_pad_soak')], default=b'pke_rsa_crt_dec_no_pad_soak', max_length=30)),
                ('input_metric_name', models.CharField(choices=[(0, b'RSA_CRT_2048_decryptions')], default=b'RSA_CRT_2048_decryptions', max_length=40)),
                ('output_ops_per_sec', models.IntegerField(default=-1, verbose_name=b'ops per sec')),
            ],
        ),
    ]
