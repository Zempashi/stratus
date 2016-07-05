# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stratus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HKVMGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('children', models.ManyToManyField(related_name='father', to='stratus.HKVMGroup')),
            ],
        ),
        migrations.AddField(
            model_name='hkvm',
            name='disk',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='hkvm',
            name='load',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='hkvm',
            name='memory',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='hkvmgroup',
            name='hkvms',
            field=models.ManyToManyField(to='stratus.HKVM'),
        ),
    ]
