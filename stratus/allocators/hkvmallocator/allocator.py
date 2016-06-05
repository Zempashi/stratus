
from __future__ import unicode_literals

import logging
import operator
from django.utils import six
from django.apps import apps


stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')


class HKVMAllocator(object):

    def __init__(self, HKVMClass = HKVM):
        self.logger = logging.getLogger(__name__)
        self.HKVMClass = HKVMClass

    def allocate(self, vms=None, hkvms=None):
        if vms is None:
            try:
                vms = VM.objects.filter(status=u'INCOMPLETE')
            except VM.DoesNotExist:
                return
        if hkvms is None:
            try:
                hkvms = self.HKVMClass.objects.filter(virtual=False)
            except HKVM.DoesNotExist:
                return
        print(vms)
        print(hkvms)
        for vm in vms:
            vm_mem = 4096
            vm_disk = 10240
            iter_weight = self._iter_hkvm_weight(hkvms, vm_mem, vm_disk)
            hkvm, weight = max(iter_weight, key=operator.itemgetter(1))
            if weight <= 0:
                self.logger.warning('\'{vm}\' cannot be allocated'
                                    ' to any hypervisor'.format(vm=vm) )
                continue
            else:
                hkvm.hkvmansiblestatus.memory -= vm_mem
                hkvm.hkvmansiblestatus.disk -= vm_disk
                vm.hkvm = hkvm
                self.logger.info('\'{}\' goes to \'{}\''.format(vm, hkvm))
                vm.save()

    def _iter_hkvm_weight(self, hkvm_iter, vm_mem, vm_disk):
        for hkvm in hkvm_iter:
            mem = hkvm.hkvmansiblestatus.memory
            disk = hkvm.hkvmansiblestatus.disk
            rest_mem = mem - vm_mem
            rest_disk = disk - vm_disk
            if rest_mem <= 10 and rest_disk <= 10:
                weight = 0
            else:
                weight = rest_mem * rest_disk
            yield (hkvm, weight)
