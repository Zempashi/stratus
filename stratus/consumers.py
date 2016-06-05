
import logging
from importlib import import_module

from .models import VM
from . import settings

class VMConsumer(object):

    def __init__(self,
                 manager_module = settings.STRATUS_MANAGER,
                 allocator_module = settings.STRATUS_ALLOCATOR):
        self.logger = logging.getLogger(__name__)
        self.manager_module = manager_module
        self.allocator_module = allocator_module
        self.MANAGER_CLS = self.import_cls(manager_module)
        self.ALLOCATOR_CLS = self.import_cls(allocator_module)
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
        self.logger.debug('VM to process \'%s\'', vm_to_create or 'default: all')
        # Refresh hypervisor status
        self.manager.hkvm_status()
        self.allocator.allocate(vm_to_create)
        try:
            self.manager.create_vm(vm_to_create)
        except BaseException:
            # TODO: Mark VM as faulty
            pass

    @staticmethod
    def import_cls(class_spec):
        try:
            return import_module(class_spec)
        except ImportError:
            mod_name, _, cls_name = class_spec.rpartition('.')
            return getattr(import_module(mod_name), cls_name)

vm_consumer = VMConsumer()
