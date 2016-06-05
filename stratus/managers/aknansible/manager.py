
from __future__ import unicode_literals

import logging
import pprint
import json

from django.utils import six
from django.utils.six.moves import filter
from django.db.models import Max
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from .models import VM, HKVM
from .models import HKVMAnsibleStatus

from . import settings
from .settings import STRATUS_ANSIBLE_INVENTORY

try:
    from django.utils import timezone as datetime
except ImportError:
    from datetime import datetime

try:
    from .ansible_helper import AnsibleHelper
except ImportError:
    if six.PY3:
        raise ValueError('Ansible is not compatible with python 3')
    else:
        raise ValueError('Please install Ansible')

if not apps.is_installed('stratus.managers.aknansible'):
    raise ImproperlyConfigured(u'You must add \'%s\' in INSTALLED_APPS'
                               % '.'.join(__name__.split('.')[:-1]))


class AknAnsibleManager(object):

    Options = namedtuple('Options',
                         ['connection', 'module_path', 'forks', 'become_user',
                          'become', 'become_method', 'check', 'extra_vars'])

    def __init__(self,
                 cache_time=settings.STRATUS_ANSIBLE_HKVM_CACHE_TIME,
                 HKVMClass=HKVMAnsibleStatus):
        self.cache_time = cache_time
        self.logger = logging.getLogger('stratus.AknAnsibleManager')
        self.HKVMClass = HKVMClass

    def create_vm(self):
        mapping_create = {}
        for hkvm in HKVM.objects.all():
            vms = VM.objects.filter(hkvm=hkvm, status='TO_CREATE')
            mapping_create[hkvm.name] = dict((vm.name, vm.args) for vm in vms)
        print(mapping_create)
        vars_ = self._action_vm_ansible(mapping_create=mapping_create)
        for hkvm_name in self._format_groups(vars_)['hkvm']:
            # Parse creation
            all_res = vars_['hostvars'][hkvm_name]['create_vm_result']
            vms_dict = dict((res['item'], res) for res in all_res['results'])
            vms_created = VM.objects.filter(hkvm__name=hkvm_name,
                                            name__in=vms_dict.keys())
            for vm in vms_created:
                res = vms_dict[vm.name]
                print(res)
                if not res.get('failed') and not res.get('skipped'):
                    vm.status = 'STOPPED'
                elif res.get('skipped'):
                    vm.error = 'Has been skipped ??? why ??'
                else:
                    vm.error = res['msg']
                vm.save()

    def hkvm_status(self, group=None, hkvm=None):
        all_hkvm = self.HKVMClass.objects.all()
        older_hkvm = all_hkvm.aggregate(Max('last_status_updated'))
        last_status = older_hkvm['last_status_updated__max']
        if last_status is not None:
            delta = (datetime.now() - last_status).total_seconds()
            self.logger.debug('HKVM info refresh have been done'
                              ' %s seconds ago' % delta)
        else:
            self.logger.debug('No HKVM info. Force refresh')
        if last_status is None or delta > self.cache_time:
            self._hkvm_vm_and_ressources(group=group, hkvm=hkvm)

    def _hkvm_vm_and_ressources(self, group=None, hkvm=None):
        variables = self._list_vm_ansible()
        groups = self._format_groups(variables)
        for hkvm_name in groups['hkvm']:
            HKVMManager = self.HKVMClass.objects
            try:
                hkvm = HKVMManager.get(name=hkvm_name)
            except HKVM.DoesNotExist:
                hkvm = HKVMManager.create(name=hkvm_name, virtual=False)
            # VM List
            hkvm_vars = variables['hostvars'][hkvm_name]
            virsh_stdout = hkvm_vars['hkvm_list_vm']['stdout_lines']
            vm_list = self._parse_virsh_list_stdout(virsh_stdout)
            self.logger.debug(pprint.pformat((hkvm, vm_list)))
            hkvm.update_vms(**vm_list)
            # Memory update
            hkvm.memory = hkvm_vars["ansible_memfree_mb"]
            # Disk update
            vgdisplay_stdout = hkvm_vars['hkvm_free_space']['stdout_lines']
            hkvm.disk = self._parse_vgdisplay_stdout(vgdisplay_stdout)
            self.logger.debug('HKVM {hkvm} has {mem} MB RAM and'
                              '{disk} MB disk left'.format(hkvm=hkvm_name,
                                                           mem=hkvm.memory,
                                                           disk=hkvm.disk))
            # Update the status date for HKVM
            hkvm.save()

    def _list_vm_ansible(self):
        ah = AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        play_src = dict(
            name="List HKVM",
            hosts='hkvm',
            remote_user='root',
            gather_facts='yes',
            tasks=[
                dict(action=dict(module='command',
                                 args='virsh list --all'),
                     register='hkvm_list_vm'),
                dict(action=dict(module='command',
                                 args='vgdisplay vg --units M'),
                     register='hkvm_free_space')])
        return ah.run_play(play_src)

    def _action_vm_ansible(self, mapping_create):
        ah = AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        play_src = dict(
            name='Create/Delete/Start/Stop VMs',
            hosts='hkvm',
            remote_user='root',
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell',
                                 args='virsh list --all'
                                      '|tail -n +3|awk \'{print $2}\''),
                     register='current_vm'),
                dict(action=dict(module='command',
                                 args='{{(mapping_create|default)'
                                      '[inventory_hostname][item]}}'),
                     with_items='{{ ((mapping_create|default)'
                                '[inventory_hostname]|default([]))'
                                '|difference(current_vm.stdout_lines'
                                '|default([])) }}',
                     register='create_vm_result'),
            ]
        )

        extra_vars = json.dumps(dict(mapping_create=mapping_create))
        ah.options_args['extra_vars'] = [extra_vars]
        return ah.run_play(play_src)

    def _parse_virsh_list_stdout(self, virsh_stdout):
        res = dict(started_vm={}, stopped_vm={})
        for line in virsh_stdout:
            tokens = (t.strip() for t in line.strip().split(' ', 2))
            tokens = list(filter(None, tokens))
            if tokens == ['Id', 'Name', 'State']:
                continue
            elif len(tokens) < 3:
                continue
            else:
                id_, vm_name, status = tokens
                if status == 'running':
                    res['started_vm'][vm_name] = {}
                elif status == 'shut off':
                    res['stopped_vm'][vm_name] = {}
                else:
                    raise ValueError('Unknown VM Status in virsh output:'
                                     ' \'{}\''.format(status))
        return res

    def _parse_vgdisplay_stdout(self, vgdisplay_stdout):
        for line in vgdisplay_stdout:
            tokens = list(filter(None, line.split(' ')))
            if not tokens[:4] == [u'Free', u'PE', u'/', u'Size']:
                continue
            else:
                return int(float(tokens[6]))
        else:
            raise ValueError('Vgdisplay Free Space Token not Found')

    def _format_groups(self, variables):
        groups = {}
        group_items = variables['hostvars']._inventory.get_groups().items()
        for group_name, group in group_items:
            groups[group_name] = [h.name for h in group.get_hosts()]
        return groups
