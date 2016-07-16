# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stratus', '0002_auto_20160705_1729'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vm',
            old_name='created',
            new_name='created_date',
        ),
        migrations.AddField(
            model_name='hkvm',
            name='error',
            field=models.CharField(max_length=10000, blank=True),
        ),
        migrations.AddField(
            model_name='vm',
            name='IP',
            field=models.GenericIPAddressField(default=None, null=True),
        ),
    ]
