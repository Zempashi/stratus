

import time
from importlib import import_module

try:
    from django.channels import Group
    from django.channels.sessions import enforce_ordering, channel_session
except ImportError:
    from channels import Group
    from channels.sessions import enforce_ordering, channel_session

from .models import VM
from . import settings

MANAGER = import_module(settings.STRATUS_MANAGER)

def create_vm(message):
    print('About to create a VM', message.content)
    manager = MANAGER.Manager()
    manager.create_vm()
    time.sleep(10)
    print('VM created', message.content)
    vm = VM.objects.get(pk=message.content['vm_pk'])
    vm.status='CREATED'
    vm.save()

def list_vm(message):
    manager = MANAGER.Manager()
    manager.list_vm()
    time.sleep(10)
