# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stratus', '0003_auto_20160726_0811'),
    ]

    operations = [
        migrations.CreateModel(
            name='GazonEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gazon_status', models.CharField(default='WAITING', max_length=100, choices=[('WAITING', 'Gazon entry need complementary info'), ('TO_CREATE', 'Gazon entry need to be created'), ('TO_DELETE', 'Gazon entry need to be deleted'), ('CREATED', 'Gazon is created for the VM'), ('NONE', 'None has to been done for gazon. Ever')])),
                ('gazon_error', models.CharField(max_length=100, blank=True)),
                ('vm', models.OneToOneField(default=None, to='stratus.VM')),
            ],
        ),
    ]
