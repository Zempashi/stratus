
from __future__ import unicode_literals

from django.utils import six
from django.db import models
from django.apps import apps

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')


class HKVMAnsibleStatus(HKVM):

    memory = models.PositiveIntegerField(null=True)
    disk = models.PositiveIntegerField(null=True)
    last_status_updated = models.DateTimeField(auto_now=True, null=True)
