from __future__ import unicode_literals

import logging
import operator
from django.utils import six
from django.apps import apps
from django.utils.module_loading import import_string

from .settings import STRATUS_HKVM_MAPPING

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')
HKVMGroup = stratus_app.get_model('HKVMGroup')

class HKVMAllocator(object):

    def __init__(self, HKVMClass = HKVM):
        self.logger = logging.getLogger(__name__)
        self.HKVMClass = HKVMClass
        if isinstance(STRATUS_HKVM_MAPPING, six.string_types):
            self.match_conf = import_string(STRATUS_HKVM_MAPPING)
        else:
            self.match_conf = STRATUS_HKVM_MAPPING

    def allocate(self, vms=None, hkvms=None):
        if vms is None:
            try:
                vms = VM.objects.filter(status=u'PENDING', error='')
            except VM.DoesNotExist:
                return
        for vm in vms:
            group = self.get_group(vm)
            iter_weight = self._iter_hkvm_weight(group.iter_keys(), vm)
            hkvm, weight = max(iter_weight, key=operator.itemgetter(1))
            if weight <= 0:
                # All weight are below zero: no hkvm can fit
                self.logger.warning('\'{vm}\' cannot be allocated'
                                    ' to any hypervisor'.format(vm=vm) )
                continue
            else:
                hkvm.hkvmansiblestatus.memory -= vm.memory
                hkvm.hkvmansiblestatus.disk -= vm.disk
                vm.hkvm = hkvm
                vm.status = 'TO_CREATE'
                self.logger.info('\'{}\' goes to \'{}\''.format(vm, hkvm))
                vm.save()

    def get_group(self, vm):
        match_conf = self.match_conf
        if callable(match_conf):
            return match_conf(vm)
        else:
            for match in match_conf:
                if match.match(vm):
                    return match.group_name

    def _iter_hkvm_weight(self, hkvm_list, vm):
        # Make inventory of all ressource
        hkvm_ressource = {}
        for hkvm in hkvm_list:
            hkvm_ressource[hkvm] = (hkvm.hkvmansiblestatus.memory,
                                    hkvm.hkvmansiblestatus.disk)
        # Substraction of al ressource already allocated but not launched
        already_allocated = VM.objects.filter(status='TO_CREATE',
                                                hkvm__in=hkvm_list)
        for vm in already_allocated:
            hkvm_mem, hkvm_disk = hkvm_ressource[vm.hkvm]
            hkvm_ressource[vm.hkvm] = (hkvm_mem - vm.memory,
                                        hkvm_mem - vm.disk)
        # Test the vm on each hypervisor. Return the weight
        # More the weight is, tthe more the hkvm will be choosen
        for hkvm, (mem, disk) in six.iteritems(hkvm_ressource):
            rest_mem = mem - vm.memory
            rest_disk = disk - vm.disk
            if rest_mem <= 10 and rest_disk <= 10:
                weight = 0
            else:
                weight = rest_mem * rest_disk
            yield (hkvm, weight)
