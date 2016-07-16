
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
    memory = models.PositiveIntegerField(null=True)
    disk = models.PositiveIntegerField(null=True)
    load = models.FloatField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    last_status = models.CharField(choices=HKVM_STATUS_ENUM,
                                    default=u'UNKNOWN', max_length=100)
    error = models.CharField(blank=True, max_length=10000)

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
        return u'{}'.format(self.name)

    __str__ = __unicode__


class HKVMGroup(models.Model):

    name = models.CharField(max_length=100, unique=True)
    children = models.ManyToManyField('HKVMGroup', related_name='father')
    hkvms = models.ManyToManyField(HKVM)

    def iter_hkvm(self):
        child_set = set()
        return self._iter_hkvm(child_set)

    def _iter_hkvm(self, child_set):
        for child in self.children.all():
            if child not in child_set:
                child_set.add(child)
                for hkvm in child.iter_hkvm():
                    yield hkvm
        for hkvm in self.hkvms.all():
            yield hkvm

    def __unicode__(self):
        children_prefix = map(lambda c: '->' + str(c), self.children.all())
        return u'{} ({})'.format(
            self.name,

            self.hkvms.all(),
            ', ->'.join(children_prefix))

    __str__ = __unicode__
