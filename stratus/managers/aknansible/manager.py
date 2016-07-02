
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

from .models import VM, HKVM, HKVMGroup
from .models import HKVMAnsibleStatus

from . import settings
from .settings import STRATUS_ANSIBLE_INVENTORY

try:
    from django.utils import timezone as datetime
except ImportError:
    from datetime import datetime

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

    @property
    def AnsibleHelper(self):
        '''Load Ansible lazily.
           Ansible make ~/.ansible when imported which could result in OSError
           Worker is specially set to have is home writable'''
        try:
            from .ansible_helper import AnsibleHelper
            return AnsibleHelper
        except ImportError:
            if six.PY3:
                raise ValueError('Ansible is not compatible with python 3')
            else:
                raise

    def create_vm(self):
        ah = self.AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        av = ActionVM()
        create = {hkvm: dict(av.vm_create(hkvm)) for hkvm in av.hkvm_create}
        remove = {hkvm: dict(av.vm_remove(hkvm)) for hkvm in av.hkvm_remove}
        extra_vars = json.dumps({'map_create': create, 'map_remove': remove})
        ah.options_args['extra_vars'] = [extra_vars]
        module_basedir = os.path.dirname(__file__)
        pb_file = os.path.join(module_basedir, 'playbooks', 'action_vm.yml')
        vars_ = ah.run_playbook(pb_file)
        self._parse_create_results(vars_, av)
        self._parse_remove_results(vars_, av)

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
        self.make_group(variables)
        groups = self._format_groups(variables)
        for hkvm_name in groups['hkvm']:
            hkvm, created = self.HKVMClass.objects.get_or_create(
                name=hkvm_name,
                defaults={'virtual': False})
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
        ah = self.AnsibleHelper(STRATUS_ANSIBLE_INVENTORY)
        module_basedir = os.path.dirname(__file__)
        pb_file = os.path.join(module_basedir, 'playbooks', 'list_hkvm.yml')
        return ah.run_playbook(pb_file)

    def _parse_create_results(self, vars_, action_obj):
        for hkvm in action_obj.hkvm_create:
            create_res = vars_['hostvars'][hkvm]['create_vm_result']
            res_dict = dict((r['item'], r) for r in create_res['results'])
            for vm in action_obj.vm_create(hkvm):
                res = res_dict.get(vm.name)
                if not res or (not res.get('failed') and not res.get('skipped')):
                    vm.status = 'STOPPED'
                    vm.error = ''
                    self.logger.info('Successfully create %s' % vm)
                elif res.get('failed'):
                    try:
                        vm.error = res['stdout']
                    except KeyError:
                        vm.error = res['msg']
                vm.save()

    def _parse_remove_results(self, vars_, action_obj):
        for hkvm in action_obj.hkvm_remove:
            undefine_res = vars_['hostvars'][hkvm.name]['undefine_vm_result']
            # destroy_res = vars_['hostvars'][hkvm.name]['destroy_vm_result']
            res_dict = dict((r['item'], r) for r in undefine_res['results'])
            for vm in action_obj.vm_remove(hkvm):
                res = res_dict.get(vm.name)
                if not res or (not res.get('failed') and not res.get('skipped')):
                    vm.status = 'DELETED'
                    vm.error = ''
                    self.logger.info('Successfully delete %s' % vm)
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

    def make_group(self, variables):
        all_groups = variables['hostvars']._inventory.get_groups()
        for name, ans_group in six.iteritems(all_groups):
            group, _ = HKVMGroup.objects.get_or_create(name=name)
            children = [HKVMGroup.objects.get_or_create(name=g.name)[0]
                        for g in ans_group.child_groups]
            group.children = children
            hkvms = [HKVM.objects.get_or_create(name=h.name)[0]
                     for h in ans_group.get_hosts()]
            group.hkvms = hkvms
            group.save()


class ActionVM(object):

    def __init__(self,):
        self.to_create = {}
        self.to_remove = {}
        for hkvm in HKVM.objects.all():
            self.to_create[hkvm] = VM.objects.filter(hkvm=hkvm, status='TO_CREATE').all()
            self.to_remove[hkvm] = VM.objects.filter(hkvm=hkvm, status='TO_DELETE').all()

    def _vm_action(action):
        def iter_vm_action(self, hkvm):
            return ((v.name, v.args) for v in getattr(self, action)[hkvm])
        return iter_vm_action

    vm_create = _vm_action('to_create')
    vm_remove = _vm_action('to_remove')

    def _hkvm_action(action):
        def iter_hkvm_action(self):
            var = getattr(self, action)
            return filter(lambda x: var[x], six.iterkeys(var))
        return iter_hkvm_action

    hkvm_create = property(_hkvm_action('to_create'))
    hkvm_remove = property(_hkvm_action('to_remove'))
