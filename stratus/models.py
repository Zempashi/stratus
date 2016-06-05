
from __future__ import unicode_literals

from django.utils import six
from django.db import models

# Create your models here.

VM_STATUS_ENUM = [  (u'UNKNOWN',  u'VM status is unknown'),
                    (u'CREATION', u'VM is currently created'),
                    (u'CREATED',  u'VM has been created'),
                    (u'STOPPED',  u'VM is stopped'),
                    (u'STARTED',  u'VM is currently running'),
                    (u'VANISHED', u'VM has disappeared without stratus action'),
                    (u'DELETED',  u'VM has been deleted'),
                    (u'TO_DELETE', u'VM has been mark for deletion'),
                    (u'INCOMPLETE', u'VM status is incomplete'),
                    (u'CREATION_FAILURE', u'VM has failed being created'),
                ]

HKVM_STATUS_ENUM = [(u'UNKNOWN',  u'HKVM status is unknown'),
                    (u'OK',       u'HKVM is running'),
                    (u'FAILURE',  u'HKVM has failed'),
                ]

class VM(models.Model):
    name = models.CharField(max_length=100)
    hkvm = models.ForeignKey('HKVM', null=True, on_delete=models.SET_NULL)
    args = models.TextField()
    status = models.CharField(choices=VM_STATUS_ENUM, default='UNKNOWN', max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (u'created',)

    def start(self):
        if self.status == u'STARTED':
            return
        elif self.status in [u'CREATED', u'STOPPED']:
            self.status = u'STARTED'
            self.save()

    def stop(self):
        if self.status == u'STOPPED':
            return
        elif self.status in [u'CREATED', u'VANISHED']:
            self.status = u'STOPPED'
            self.save()

    def erase(self):
        if self.status in [u'DELETED', 'VANISHED']:
            self.delete()
        elif self.status == u'TO_DELETE':
            return
        elif self.status in [u'STARTED', u'STOPPED']:
            self.status = u'VANISHED'
            self.save()

    def __str__(self):
        return u'<VM: {}>'.format(self.name)


class HKVM(models.Model):
    name = models.CharField(max_length=100, unique=True)
    virtual = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_status_updated = models.DateTimeField(auto_now_add=True, null=True)
    last_status = models.CharField(choices=HKVM_STATUS_ENUM, default=u'UNKNOWN', max_length=100)

    def __str__(self):
        return u'<HKVM: {}>'.format(self.name)

    def update_vms(self, started_vm, stopped_vm):
        processed_vm = set()
        for vm in self.vm_set.all():
            if vm in started_vm:
                vm.start()
            elif vm in stopped_vm:
                vm.stop()
            else:
                vm.erase()
            processed_vm.add(vm.name)
        for vm in six.viewkeys(started_vm) - processed_vm:
            VM.objects.create(name=vm, hkvm=self, status='STARTED')
        for vm in six.viewkeys(stopped_vm) - processed_vm:
            VM.objects.create(name=vm, hkvm=self, status='STOPPED')
