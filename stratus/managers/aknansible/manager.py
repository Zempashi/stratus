
from __future__ import unicode_literals

from django.utils import six
from django.utils.six.moves import filter

import logging
import pprint

try:
    from django.utils import timezone as datetime
except ImportError:
    from datetime import datetime

from collections import namedtuple

if six.PY2:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars import VariableManager
    from ansible.inventory import Inventory
    from ansible.playbook.play import Play
    from ansible.executor.task_queue_manager import TaskQueueManager

from django.db.models import Max

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

if not apps.is_installed('stratus.managers.aknansible'):
    raise ImproperlyConfigured(u'You must add \'%s\' in INSTALLED_APPS'
                               % '.'.join(__name__.split('.')[:-1]))

from .models import VM, HKVM
from .models import HKVMAnsibleStatus

from . import settings
from .settings import STRATUS_ANSIBLE_INVENTORY

class AknAnsibleManager(object):

    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check'])

    def __init__(self,
                cache_time=settings.STRATUS_ANSIBLE_HKVM_CACHE_TIME,
                HKVMClass = HKVMAnsibleStatus):
        self.cache_time = cache_time
        self.logger = logging.getLogger('stratus.AknAnsibleManager')
        self.HKVMClass = HKVMClass

    def create_vm(self):
        pass

    def hkvm_status(self, group=None, hkvm=None):
        all_hkvm = self.HKVMClass.objects.all()
        older_hkvm = all_hkvm.aggregate(Max('last_status_updated'))
        last_status = older_hkvm['last_status_updated__max']
        if last_status is not None:
            delta = (datetime.now() - last_status).total_seconds()
            self.logger.debug('HKVM info refresh have been done'
                              ' %s seconds ago'% delta)
        else:
            self.logger.debug('No HKVM info. Force refresh')
        if last_status is None or delta > self.cache_time:
            self.hkvm_vm_and_ressources(group=group, hkvm=hkvm)

    def hkvm_vm_and_ressources(self, group=None, hkvm=None):
        variables = self.list_vm_ansible()
        groups = self.format_groups(variables)
        for hkvm_name in groups['hkvm']:
            HKVMManager = self.HKVMClass.objects
            try:
                hkvm = HKVMManager.get(name=hkvm_name)
            except HKVM.DoesNotExist:
                hkvm = HKVMManager.create(name=hkvm_name, virtual=False)
            ### VM List
            hkvm_vars = variables['hostvars'][hkvm_name]
            virsh_stdout = hkvm_vars['hkvm_list_vm']['stdout_lines']
            vm_list = self.parse_virsh_list_stdout(virsh_stdout)
            self.logger.debug(pprint.pformat((hkvm, vm_list)))
            hkvm.update_vms(**vm_list)
            ### Memory update
            hkvm.memory = hkvm_vars["ansible_memfree_mb"]
            ### Disk update
            vgdisplay_stdout = hkvm_vars['hkvm_free_space']['stdout_lines']
            hkvm.disk = self.parse_vgdisplay_stdout(vgdisplay_stdout)
            self.logger.debug('HKVM {hkvm} has {mem} MB RAM'
                            ' and {disk} MB disk left'.format(hkvm=hkvm_name,
                                                              mem=hkvm.memory,
                                                              disk=hkvm.disk))
            ### Update the status date for HKVM
            hkvm.save()

    def list_vm_ansible(self):
        ansible_args = self.initialize_ansible(STRATUS_ANSIBLE_INVENTORY)
        play_source = dict(
            name = "Ansible Play",
            hosts = 'hkvm',
            remote_user = 'root',
            gather_facts = 'yes',
            tasks = [
                dict(action=dict(module='command', args='virsh list --all'), register='hkvm_list_vm'),
                dict(action=dict(module='command', args='vgdisplay vg --units M'), register='hkvm_free_space'),
            ]
        )
        play = Play().load(play_source, loader = ansible_args['loader'],
                            variable_manager = ansible_args['variable_manager'])
        options = self.Options(connection='smart', module_path=None, forks=100, become=None, become_method=None, become_user=None, check=False)
        ansible_args.update(stdout_callback='default', passwords=dict(conn_pass='playground'), options=options)
        tqm = None
        try:
            tqm = TaskQueueManager(**ansible_args)
            tqm.run(play)
            return ansible_args['variable_manager'].get_vars(ansible_args['loader'])
        finally:
            if tqm is not None:
                tqm.cleanup()

    def parse_virsh_list_stdout(self, virsh_stdout):
        res = dict(started_vm={}, stopped_vm={})
        for line in virsh_stdout:
            tokens = ( t.strip() for t in line.strip().split(' ', 2) )
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

    def parse_vgdisplay_stdout(self, vgdisplay_stdout):
        for line in vgdisplay_stdout:
            tokens = list(filter(None, line.split(' ')))
            if not tokens[:4] == [u'Free', u'PE', u'/', u'Size']:
                continue
            else:
                return int(float(tokens[6]))
        else:
            raise ValueError('Vgdisplay Free Space Token not Found')


    def format_groups(self, variables):
        groups = {}
        for group_name, group in variables['hostvars']._inventory.get_groups().items():
            groups[group_name] = [h.name for h in group.get_hosts()]
        return groups

    def initialize_ansible(self, inventory_file):
        variable_manager = VariableManager()
        loader = DataLoader()
        inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=inventory_file)
        variable_manager.set_inventory(inventory)
        return dict(variable_manager=variable_manager,
                    loader=loader,
                    inventory=inventory)
