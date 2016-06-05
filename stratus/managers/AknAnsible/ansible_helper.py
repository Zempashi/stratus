#!/usr/bin/env python2

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'verbosity'])

def run_ansible(play_source, inventory_file):
    variable_manager = VariableManager()
    loader = DataLoader()
    options = Options(connection='smart', module_path=None, forks=100, become=None, become_method=None, become_user=None, check=False, verbosity=4)


    # create inventory and pass to var manager
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=inventory_file)
    variable_manager.set_inventory(inventory)

    # create play with tasks
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # actually run it
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=dict(conn_pass='playground'),
                  stdout_callback='default',
              )

        result = tqm.run(play)
        variables = variable_manager.get_vars(loader)
        return variables

    finally:
        if tqm is not None:
            tqm.cleanup()
