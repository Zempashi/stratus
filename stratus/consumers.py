
from __future__ import absolute_import, unicode_literals

import logging
from django.utils.module_loading import import_string

from .models import VM
from . import settings


class VMConsumer(object):

    def __init__(self,
                 manager_module=settings.STRATUS_MANAGER,
                 allocator_module=settings.STRATUS_ALLOCATOR):
        self.logger = logging.getLogger(__name__)
        self.manager_module = manager_module
        self.allocator_module = allocator_module
        self.MANAGER_CLS = import_string(manager_module)
        self.ALLOCATOR_CLS = import_string(allocator_module)
        self.manager = self.MANAGER_CLS()
        self.allocator = self.ALLOCATOR_CLS()

    def create_vms(self, message):
        self.logger.debug('Receive order to create VMs with these params %s',
                          message.content)
        try:
            vm_id_to_create = list(message.content['vm_pk'])
            vm_to_create = VM.objects.get(pk__in=tuple(vm_id_to_create))
        except (TypeError, KeyError):
            vm_to_create = None
        self.logger.debug('VM to process \'%s\'', vm_to_create or 'all')
        # Refresh hypervisor status
        self.manager.hkvm_status()
        self.allocator.allocate(vm_to_create)
        try:
            self.manager.create_vm()
        except BaseException:
            # TODO: Mark VM as faulty

            raise

vm_consumer = VMConsumer()
