from __future__ import unicode_literals

import multiprocessing
import signal
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.utils.vars import load_extra_vars
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.inventory.group import Group
from ansible.playbook import Playbook
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor


class AnsibleHelper(multiprocessing.Process):

    Options = namedtuple('Options',
                         ['connection', 'module_path', 'forks', 'become_user',
                          'become', 'become_method', 'check', 'extra_vars',
                          'listhosts', 'listtasks', 'listtags', 'syntax',
                         ])

    def __init__(self, inventory_file):
        self.suppress_serializers = True
        self.variable_manager = vm = VariableManager()
        self.loader = DataLoader()
        self.inventory = Inventory(loader=self.loader,
                                   variable_manager=vm,
                                   host_list=inventory_file)
        vm.set_inventory(self.inventory)
        self.options_args = dict(connection='smart',
                                 module_path=None,
                                 forks=100,
                                 become=None,
                                 become_method=None,
                                 become_user=None,
                                 check=False,
                                 listhosts=False,
                                 listtasks=False,
                                 listtags=False,
                                 syntax=False,
                                 extra_vars={})

    def run_play(self, *args, **kwargs):
        self.queue = queue = multiprocessing.Queue()
        super(AnsibleHelper, self).__init__(
                targe=self._run,
                args=(self._run_play, queue, args, kwargs))
        return self._launch()

    def run_playbook(self, *args, **kwargs):
        self.queue = queue = multiprocessing.Queue()
        super(AnsibleHelper, self).__init__(
                target=self._run,
                args=(self._run_playbook, queue, args, kwargs))
        return self._launch()

    def _run(self, func, queue, args, kwargs):
        # Restore default signal handler
        # By defaut django-channel worker ignore SIGTERM
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        res = func(*args, **kwargs)
        self.suppress_buggy_serializers()
        queue.put(res)

    def _launch(self):
        self.daemon = False
        self.start()
        self.suppress_buggy_serializers()
        try:
            res = self.queue.get(timeout = 600)
        except multiprocessing.TimeoutError:
            raise
        else:
            return res
        finally:
            try:
                self.join(10)
            except multiprocessing.TimeoutError:
                self.terminate()

    def suppress_buggy_serializers(self):
        if not self.suppress_serializers:
            return
        if hasattr(VariableManager, '__getstate__'):
            del VariableManager.__getstate__
            del VariableManager.__setstate__
        if hasattr(Group, '__getstate__'):
            del Group.__getstate__
            del Group.__setstate__

    def _run_play(self, play_src):
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
                passwords=dict(),
                stdout_callback='default')
            tqm.run(play)
            return vm.get_vars(self.loader)
        finally:
            if tqm is not None:
                tqm.cleanup()

    def _run_playbook(self, playbook):
        self.options = options = self.Options(**self.options_args)
        vm = self.variable_manager
        vm.extra_vars = load_extra_vars(loader=self.loader, options=options)
        pbe = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=vm,
            loader=self.loader,
            options=options,
            passwords=dict(),
        )
        pbe.run()
        return vm.get_vars(self.loader)
