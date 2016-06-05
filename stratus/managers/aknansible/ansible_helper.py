from __future__ import unicode_literals

from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.utils.vars import load_extra_vars
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executoranager import TaskQueueManager


class AnsibleHelper(object):

    Options = namedtuple('Options',
                         ['connection', 'module_path', 'forks', 'become_user'
                          'become', 'become_method', 'check', 'extra_vars'])

    def __init__(self, inventory_file):
        self.variable_manager = vm = VariableManager()
        self.loader = DataLoader()
        self.inventory = Inventory(loader=self.loader,
                                   variable_manager=vm,
                                   host_list=self.inventory_file)
        vm.set_inventory(self.inventory)
        self.options_args = dict(connection='smart',
                                 module_path=None,
                                 forks=100,
                                 become=None,
                                 become_method=None,
                                 become_user=None,
                                 check=False,
                                 extra_vars={})

    def run_play(self, play_src):
        self.options = options = self.Options(**self.options_args)
        vm = self.variable_manager
        vm.extra_vars = load_extra_vars(loader=self.loader, options=options)
        play = Play().load(play_src, loader=self.loader, variable_manager=vm)
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=vm,
                loader=self.loader,
                options=options,
                stdout_callback='default')
            tqm.run(play)
            return vm.get_vars(self.loader)
        finally:
            if tqm is not None:
                tqm.cleanup()
