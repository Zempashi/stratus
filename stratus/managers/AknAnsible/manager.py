
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

from django.apps import apps

from .settings import STRATUS_ANSIBLE_INVENTORY
from .ansible_helper import run_ansible

stratus_app = apps.get_app_config('stratus')
VM = stratus_app.get_model('VM')
HKVM = stratus_app.get_model('HKVM')

class AknAnsible(object):

    def __init__(self):
        pass

    def create_vm(self):
        pass

    def list_vm(self, group=None, hkvm=None):
        print(STRATUS_ANSIBLE_INVENTORY)
        variables = run_ansible(
            play_source = dict(
                name = "Ansible Play",
                hosts = 'hkvm',
                remote_user = 'root',
                gather_facts = 'no',
                tasks = [
                    dict(action=dict(module='command', args='virsh list'), register='hkvm_list_vm'),
                    dict(action=dict(module='debug', args=dict(msg='{{hkvm_list_vm.stdout_lines}}')))
                ]
            ),
            inventory_file=STRATUS_ANSIBLE_INVENTORY)
        for group in variables['hostvars']._inventory.get_groups().values():
            print(group.get_hosts())
        print(variables)
