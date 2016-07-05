from __future__ import unicode_literals

import logging
import operator
import traceback
from django.utils import six
from django.apps import apps
from django.utils.module_loading import import_string

from .settings import STRATUS_HKVM_MAPPING
import mapping

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')
HKVMGroup = stratus_app.get_model('HKVMGroup')


class HKVMAllocator(object):

    def __init__(self, HKVMClass=HKVM):
        self.logger = logging.getLogger(__name__)
        self.HKVMClass = HKVMClass
        if isinstance(STRATUS_HKVM_MAPPING, six.string_types):
            self.match_conf = import_string(STRATUS_HKVM_MAPPING)
        else:
            self.match_conf = STRATUS_HKVM_MAPPING

    def allocate(self, vms=None):
        if vms is None:
            try:
                vms = VM.objects.filter(status=u'PENDING', error='')
            except VM.DoesNotExist:
                return
        self.logger.debug('All VM to allocate \'{}\''.format(vms))
        for vm in vms:
            self._allocate_single_vm(vm)

    def get_group(self, vm):
        match_conf = self.match_conf
        if callable(match_conf):
            return match_conf(vm.name)
        else:
            for map_match in match_conf:
                if map_match.match(vm.name):
                    return map_match.group_name
            else:
                raise ValueError('Cannot find a group to '
                                 'allocate this VM: \'{}\''.format(vm))

    def _allocate_single_vm(self, vm):
        try:
            group_id = self.get_group(vm)
            if group_id is None:
                # No allocation has to be made
                pass
            elif group_id is mapping._all_:
                all_hkvm = self.HKVMClass.objects.filter(virtual=False).all()
                self._allocate_to_hkvms(vm, all_hkvm)
            elif isinstance(group_id, six.string_types):
                group = HKVMGroup.objects.get(name=group_id)
                self.logger.debug('group \'{}\' has been selected for \'{}\''
                                  ''.format(group, vm))
                self._allocate_to_hkvms(vm, group.iter_hkvm())
            else:
                raise TypeError(
                    'Can\'t use the group \'{}\' of type \'{}\''.format(
                        group_id, type(group_id)))
        except Exception as exc:
            exc_string = traceback.format_exception_only(type(exc), exc)[0]
            self.logger.debug('Cannot allocate VM \'{}\' because of: {}'.format(vm, exc_string))
            vm.error = exc_string
            vm.save()

    def _allocate_to_hkvms(self, vm, hkvms):
        iter_weight = self._iter_hkvm_weight(hkvms, vm)
        hkvm, weight = max(iter_weight, key=operator.itemgetter(1))
        if weight <= 0:
            # All weight are below zero: no hkvm can fit
            self.logger.warning('\'{vm}\' cannot be allocated'
                                ' to any hypervisor'.format(vm=vm))
            return
        else:
            hkvm.memory -= vm.memory
            hkvm.disk -= vm.disk
            vm.hkvm = hkvm
            vm.status = 'TO_CREATE'
            self.logger.info('\'{}\' goes to \'{}\''.format(vm, hkvm))
            vm.save()

    def _iter_hkvm_weight(self, hkvm_list, vm):
        # Make inventory of all ressource
        hkvm_ressource = {}
        for hkvm in hkvm_list:
            hkvm_ressource[hkvm] = (hkvm.memory,
                                    hkvm.disk,
                                    hkvm.load)
        # Substraction of al ressource already allocated but not launched
        already_allocated = VM.objects.filter(status='TO_CREATE',
                                              hkvm__in=hkvm_list)
        for vm in already_allocated:
            hkvm_mem, hkvm_disk, hkvm_load = hkvm_ressource[vm.hkvm]
            hkvm_ressource[vm.hkvm] = (hkvm_mem - vm.memory,
                                       hkvm_mem - vm.disk,
                                       hkvm_load)
        # Test the vm on each hypervisor. Return the weight
        # More the weight is, tthe more the hkvm will be choosen
        for hkvm, (mem, disk, load) in six.iteritems(hkvm_ressource):
            rest_mem = mem - vm.memory
            rest_disk = disk - vm.disk
            if rest_mem <= 10 and rest_disk <= 10:
                weight = 0
            else:
                weight = (rest_mem * rest_disk) / ((1 + load) * mem * disk)
            yield (hkvm, weight)
