
from __future__ import absolute_import, unicode_literals

import logging
from django.db import models
from ..signals import vm_allocated,\
                        vm_to_create,\
                        vm_created,\
                        vm_deleted,\
                        vm_start,\
                        vm_stop

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

logger = logging.getLogger(__name__)

class VM(models.Model):
    name = models.CharField(max_length=100)
    hkvm = models.ForeignKey('HKVM', null=True, on_delete=models.SET_NULL)
    args = models.TextField(blank=True)
    memory = models.PositiveIntegerField(null=True)
    disk = models.PositiveIntegerField(null=True)
    IP = models.GenericIPAddressField(null=True, default=None)
    status = models.CharField(choices=VM_STATUS_ENUM, default='PENDING', max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    error = models.CharField(blank=True, max_length=100)


    ####
    #  From here, method defining the FSM.
    #  Futur developer: find a balance between:
    #    - security, raising error when impossible case show up
    #    - flexibility, letting all happen, to let plugin creation be easy
    #          and full modification of the FSM possible with plugins.
    ###

    def start(self):
        if self.status in [u'STOPPED', u'VANISHED']:
            self.status = u'STARTED'
            vm_start.send(sender=VM.__class__, vm=self)
            self.save()

    def stop(self):
        if self.status in [u'STARTED', u'VANISHED']:
            self.status = u'STOPPED'
            vm_stop.send(sender=VM.__class__, vm=self)
            self.save()

    def erase(self):
        if self.status in [u'PENDING', u'DELETED', 'VANISHED']:
            self.delete()
        elif self.status == u'TO_DELETE':
            return
        elif self.status in [u'TO_CREATE', u'STARTED', u'STOPPED']:
            self.status = u'TO_DELETE'

    def deleted(self):
        if self.status in [u'TO_DELETE', u'VANISHED']:
            self.status = u'DELETED'
            vm_deleted.send(sender=VM.__class__, vm=self)
            if self.status == u'DELETED':
                logger.info('Successfully delete %s' % self)
            self.save()
        else:
            raise ValueError('VM deleted, but no order were given')

    def disappear(self):
        if self.status in [u'STARTED', u'STOPPED']:
            self.status = u'VANISHED'

    def allocated(self):
        if self.status == u'PENDING':
            self.status = u'TO_CREATE'
            vm_allocated.send(sender=VM.__class__, vm=self)
            self.error = ''
            self.save()

    def created(self, status='STOPPED'):
        if self.status == u'TO_CREATE':
            if status in [u'STOPPED', u'STARTED']:
                self.status = status
                vm_created.send(sender=VM.__class__, vm=self)
                if self.status in [u'STOPPED', u'STARTED']:
                    logger.info('Successfully create %s' % self)
                self.save()
            else:
                raise ValueError('Cannot create a VM in this state')
        else:
            raise ValueError('VM Created, but no order were given')

    def __unicode__(self):
        return u'{}'.format(self.name)

    __str__ = __unicode__
