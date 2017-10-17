# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='antenna',
            name='antenna_type',
            field=models.CharField(max_length=15, choices=[(b'dipole', b'Dipole'), (b'yagi', b'Yagi'), (b'helical', b'Helical'), (b'parabolic', b'Parabolic'), (b'vertical', b'Verical')]),
        ),
    ]
