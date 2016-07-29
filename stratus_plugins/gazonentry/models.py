
from __future__ import absolute_import, unicode_literals


from django.utils import six
from django.db import models
from django.apps import apps

try:
    from django.channels import Channel
except ImportError:
    from channels import Channel

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')

GAZON_STATUS_ENUM = [ (u'WAITING', u'Gazon entry need complementary info'),
                      (u'TO_CREATE', u'Gazon entry need to be created'),
                      (u'TO_DELETE', u'Gazon entry need to be deleted'),
                      (u'CREATED', u'Gazon is created for the VM'),
                      (u'DELETED', u'Gazon is deleted for the VM'),
                      (u'NONE', u'None has to been done for gazon. Ever'), ]


class GazonEntry(models.Model):

    vm = models.OneToOneField(VM, default=None)

    gazon_status = models.CharField(choices=GAZON_STATUS_ENUM, default='WAITING', max_length=100)
    gazon_error = models.CharField(blank=True, max_length=100)

    def delete_vm(self):
        if self.gazon_status in [u'CREATED', u'TO_CREATE']:
            self.gazon_status = u'TO_DELETE'
            Channel(u'gazonentry').send({})
            self.save()
