
from __future__ import unicode_literals

from django.utils import six

import logging
import pprint


from collections import namedtuple
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

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')

logger = logging.getLogger('stratus.AknAnsibleManager')

from .settings import STRATUS_ANSIBLE_INVENTORY

class AknAnsibleManager(object):

    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check'])

    def __init__(self):
       pass

    def create_vm(self):
        pass


    def hkvm_status(self, group=None, hkvm=None):
        older_hkvm = HKVM.objects.all().aggregate(Max('last_status_updated'))
        print(older_hkvm)
        last_status = older_hkvm['last_status_updated__max']
        if last_status is None or last_status is not None:
            self.list_vm(group=group, hkvm=hkvm)

    def list_vm(self, group=None, hkvm=None):
        variables = self.list_vm_ansible()
        groups = self.format_groups(variables)
        for hkvm in groups['hkvm']:
            virsh_stdout = variables['hostvars'][hkvm]['hkvm_list_vm']['stdout_lines']
            vm_list = self.parse_virsh_list_stdout(virsh_stdout)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(pprint.pformat((hkvm, vm_list)))
            try:
                hkvm = HKVM.objects.get(name=hkvm)
            except HKVM.DoesNotExist:
                hkvm = HKVM.objects.create(name=hkvm, virtual=False)
            hkvm.update_vms(**vm_list)

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
            tokens = [ t.strip() for t in line.strip().split(' ', 2) if t.strip() ]
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
                    raise ValueError('Unknown VM Status in virsh output: \'{}\''.format(status))
        return res

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
