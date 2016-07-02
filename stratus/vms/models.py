
from __future__ import absolute_import, unicode_literals

from django.db import models

VM_STATUS_ENUM = [  (u'PENDING',   u'VM need to be checked'),
                    (u'TO_CREATE', u'VM is ready to be created'),
                    (u'STOPPED',   u'VM is stopped'),
                    (u'STARTED',   u'VM is currently running'),
                    (u'TO_STOP',   u'VM is required to be stopped'),
                    (u'TO_START',  u'VM is required to be started'),
                    (u'VANISHED',  u'VM has disappeared without stratus action'),
                    (u'TO_DELETE', u'VM has been marked for deletion'),
                    (u'DELETED',   u'VM has been deleted'),
                ]

class VM(models.Model):
    name = models.CharField(max_length=100)
    hkvm = models.ForeignKey('HKVM', null=True, on_delete=models.SET_NULL)
    args = models.TextField(blank=True)
    memory = models.PositiveIntegerField(null=True)
    disk = models.PositiveIntegerField(null=True)
    status = models.CharField(choices=VM_STATUS_ENUM, default='PENDING', max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    error = models.CharField(blank=True, max_length=100)

    def start(self):
        if self.status == u'STARTED':
            return
        elif self.status in [u'CREATED', u'STOPPED']:
            self.status = u'STARTED'

    def stop(self):
        if self.status == u'STOPPED':
            return
        elif self.status in [u'CREATED', u'VANISHED']:
            self.status = u'STOPPED'

    def erase(self):
        if self.status in [u'PENDING', u'DELETED', 'VANISHED']:
            self.delete()
        elif self.status == u'TO_DELETE':
            return
        elif self.status in [u'TO_CREATE', u'STARTED', u'STOPPED']:
            self.status = u'TO_DELETE'

    def disappear(self):
        if self.status in [u'STARTED', u'STOPPED']:
            self.status = u'VANISHED'

    def __unicode__(self):
        return u'{}'.format(self.name)

    __str__ = __unicode__
