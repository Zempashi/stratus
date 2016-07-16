
from __future__ import absolute_import, unicode_literals

import logging
import django.dispatch
from django.utils import six
from django.conf import settings
from django.utils.module_loading import import_string

from .models import VM, HKVM
from .signals import before_action

class VMConsumer(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.manager_module = getattr(settings, 'STRATUS_MANAGER',
            'stratus.managers.aknansible.manager.AknAnsibleManager')
        self.allocator_module = getattr(settings, 'STRATUS_ALLOCATOR',
            'stratus.allocators.hkvmallocator.allocator.HKVMAllocator')
        self.MANAGER_CLS = import_string(self.manager_module)
        self.ALLOCATOR_CLS = import_string(self.allocator_module)
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
            self.manager.create_vm(action = ActionVM())
        except BaseException:
            # TODO: Mark VM as faulty
            raise

def get_consumer():
    return VMConsumer()

class ActionVM(object):

    def __init__(self, HKVMClass=HKVM):
        self.HKVMClass = HKVMClass
        self.to_create = {}
        self.to_delete = {}
        vm_to_create = [vm for vm in VM.objects.filter(status=u'TO_CREATE',
                                          hkvm__virtual=False).all()]
        vm_to_delete = [vm for vm in VM.objects.filter(status=u'TO_DELETE',
                                          hkvm__virtual=False).all()]
        before_action.send(sender=self.__class__,
                           create_list=vm_to_create,
                           delete_list=vm_to_delete)
        for vm in vm_to_create:
            self.to_create.setdefault(vm.hkvm, []).append(vm)
        for vm in vm_to_delete:
            self.to_delete.setdefault(vm.hkvm, []).append(vm)

    def _vm_action(action):
        def iter_vm_action(self, hkvm):
            return (vm for vm in getattr(self, action)[hkvm])
        return iter_vm_action

    vm_create = _vm_action('to_create')
    vm_remove = _vm_action('to_delete')

    def _hkvm_action(action):
        def iter_hkvm_action(self):
            var = getattr(self, action)
            return filter(lambda x: var[x], six.iterkeys(var))
        return iter_hkvm_action

    hkvm_create = property(_hkvm_action('to_create'))
    hkvm_remove = property(_hkvm_action('to_delete'))
