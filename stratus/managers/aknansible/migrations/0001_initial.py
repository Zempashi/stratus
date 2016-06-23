# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stratus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HKVMAnsibleStatus',
            fields=[
                ('hkvm_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='stratus.HKVM')),
                ('memory', models.PositiveIntegerField(null=True)),
                ('disk', models.PositiveIntegerField(null=True)),
                ('last_status_updated', models.DateTimeField(auto_now=True, null=True)),
            ],
            bases=('stratus.hkvm',),
        ),
    ]
