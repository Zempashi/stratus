
import logging
from django.utils import six
from django.apps import apps

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')
HKVMGroup = stratus_app.get_model('HKVMGroup')

from ..aknansible.manager import ActionVM

class TestManager(object):

    def __init__(self, HKVMClass=HKVM):
        self.logger = logging.getLogger('stratus.TestManager')
        self.HKVMClass = HKVMClass
        self.hkvm_mapping_vm = None

    def hkvm_status(self):
        if self.hkvm_mapping_vm is None:
            # Load initial value
            self.hkvm_mapping_vm = {'hkvm1' : {'vm1': 'is'}}
        for hkvm_name, vms in six.iteritems(self.hkvm_mapping_vm):
            hkvm, created = self.HKVMClass.objects.get_or_create(
                name=hkvm_name,
                defaults={'virtual': False})
            hkvm.update_vms(started_vm=vms, stopped_vm={})
            hkvm.memory = 20480
            hkvm.disk = 102400
            hkvm.load = 0.2
            hkvm.save()

    def create_vm(self):
        av = ActionVM(HKVMClass=self.HKVMClass)
        for hkvm in av.hkvm_remove:
            hkvm_map = self.hkvm_mapping_vm.get(hkvm, {})
            for vm in av.vm_remove(hkvm):
                vm_name = vm.name
                if vm_name in hkvm_map:
                    del hkvm_map[vm_name]
        for hkvm in av.hkvm_create:
            hkvm_map = self.hkvm_mapping_vm.get(hkvm, {})
            for vm in av.vm_create(hkvm):
                hkvm_map[vm.name] = vm.args
