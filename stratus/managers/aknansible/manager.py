
from __future__ import unicode_literals

import os
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
        raise

if not apps.is_installed('stratus.managers.aknansible'):
    raise ImproperlyConfigured(u'You must add \'%s\' in INSTALLED_APPS'
                               % '.'.join(__name__.split('.')[:-1]))


class AknAnsibleManager(object):

    def __init__(self,
                 cache_time=settings.STRATUS_ANSIBLE_HKVM_CACHE_TIME,
                 HKVMClass=HKVMAnsibleStatus):
        self.cache_time = cache_time
        self.logger = logging.getLogger('stratus.AknAnsibleManager')
        self.HKVMClass = HKVMClass

    def create_vm(self):
        action_dict = ad = {'create': {}, 'remove': {}}
        for hkvm in HKVM.objects.all():
            ad['create'][hkvm] = VM.objects.filter(hkvm=hkvm, status='TO_CREATE')
            ad['remove'][hkvm] = VM.objects.filter(hkvm=hkvm, status='TO_DELETE')

        vars_ = self._action_vm_ansible(action_dict)
        self._parse_action_results(vars_, action_dict)

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
            self.logger.debug('HKVM {hkvm} has {mem} MB RAM and '
                              '{disk} MB disk left'.format(hkvm=hkvm_name,
                                                           mem=hkvm.memory,
                                                           disk=hkvm.disk))
            # Update the status date for HKVM
            hkvm.save()

    def _list_vm_ansible(self):
        ah = AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        module_basedir = os.path.dirname(__file__)
        pb_file = os.path.join(module_basedir, 'playbooks', 'list_hkvm.yml')
        return ah.run_playbook(pb_file)

    def _action_vm_ansible(self, action_dict):
        ah = AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        action_map = {}
        for action in ['create', 'remove']:
            action_map[action + '_map'] = map_ = {}
            for hkvm, vm_list in six.iteritems(action_dict[action]):
                map_[hkvm.name] = dict((v.name, v.args) for v in vm_list)

        ah.options_args['extra_vars'] = [json.dumps(action_map)]
        # ah.options_args['check'] = True
        module_basedir = os.path.dirname(__file__)
        pb_file = os.path.join(module_basedir, 'playbooks', 'action_vm.yml')
        return ah.run_playbook(pb_file)

    def _parse_action_results(self, vars_, action_dict):
        self._parse_create_results(vars_, action_dict['create'])
        self._parse_remove_results(vars_, action_dict['remove'])

    def _parse_create_results(self, vars_, action_create):
        for hkvm, vm_list in six.iteritems(action_create):
            create_res = vars_['hostvars'][hkvm.name]['create_vm_result']
            res_dict = dict((r['item'], r) for r in create_res['results'])
            for vm in vm_list:
                res = res_dict.get(vm.name)
                if not res or (not res.get('failed') and not res.get('skipped')):
                    vm.status = 'STOPPED'
                    vm.error = ''
                    self.logger.info('Successfully create %s'%vm)
                elif res.get('failed'):
                    try:
                        vm.error = res['stdout']
                    except KeyError:
                        vm.error = res['msg']
                vm.save()

    def _parse_remove_results(self, vars_, action_remove):
        for hkvm, vm_list in six.iteritems(action_remove):
            undefine_res = vars_['hostvars'][hkvm.name]['undefine_vm_result']
            destroy_res = vars_['hostvars'][hkvm.name]['destroy_vm_result']
            res_dict = dict((r['item'], r) for r in undefine_res['results'])
            for vm in vm_list:
                res = res_dict.get(vm.name)
                if not res or (not res.get('failed') and not res.get('skipped')):
                    vm.status = 'DELETED'
                    vm.error = ''
                    self.logger.info('Successfully delete %s'%vm)
                elif res.get('failed'):
                    vm.error = json.dumps(res).encode('utf-8')
                vm.save()

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
