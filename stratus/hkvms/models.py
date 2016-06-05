
from __future__ import absolute_import, unicode_literals

from django.utils import six
from django.db import models

from ..vms.models import VM

HKVM_STATUS_ENUM = [(u'UNKNOWN',  u'HKVM status is unknown'),
                    (u'OK',       u'HKVM is running'),
                    (u'FAILURE',  u'HKVM has failed'),
                ]


class HKVM(models.Model):
    name = models.CharField(max_length=100, unique=True)
    virtual = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    last_status = models.CharField(choices=HKVM_STATUS_ENUM,
                                    default=u'UNKNOWN', max_length=100)

    def update_vms(self, started_vm, stopped_vm):
        processed_vm = set()
        for vm in self.vm_set.all():
            if vm in started_vm:
                vm.start()
            elif vm in stopped_vm:
                vm.stop()
            else:
                vm.disappear()
            processed_vm.add(vm.name)
        for vm in six.viewkeys(started_vm) - processed_vm:
            VM.objects.create(name=vm, hkvm=self, status='STARTED')
        for vm in six.viewkeys(stopped_vm) - processed_vm:
            VM.objects.create(name=vm, hkvm=self, status='STOPPED')

    def __unicode__(self):
        return u'<HKVM: {}>'.format(self.name)

    __str__ = __unicode__
