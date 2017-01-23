# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-08 15:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_satellite_manual_tle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='station',
            name='antenna',
            field=models.ManyToManyField(blank=True, help_text=b'If you want to add a new Antenna contact <a href="https://community.satnogs.org/" target="_blank">SatNOGS Team</a>', to='base.Antenna'),
        ),
    ]
