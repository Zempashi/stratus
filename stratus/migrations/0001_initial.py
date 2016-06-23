# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HKVM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('virtual', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('last_status', models.CharField(default='UNKNOWN', max_length=100, choices=[('UNKNOWN', 'HKVM status is unknown'), ('OK', 'HKVM is running'), ('FAILURE', 'HKVM has failed')])),
            ],
        ),
        migrations.CreateModel(
            name='VM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('args', models.TextField(blank=True)),
                ('memory', models.PositiveIntegerField(null=True)),
                ('disk', models.PositiveIntegerField(null=True)),
                ('status', models.CharField(default='PENDING', max_length=100, choices=[('PENDING', 'VM need to be checked'), ('TO_CREATE', 'VM is ready to be created'), ('STOPPED', 'VM is stopped'), ('STARTED', 'VM is currently running'), ('TO_STOP', 'VM is required to be stopped'), ('TO_START', 'VM is required to be started'), ('VANISHED', 'VM has disappeared without stratus action'), ('TO_DELETE', 'VM has been marked for deletion'), ('DELETED', 'VM has been deleted')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('error', models.CharField(max_length=100, blank=True)),
                ('hkvm', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='stratus.HKVM', null=True)),
            ],
        ),
    ]
