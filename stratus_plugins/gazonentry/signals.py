
from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.dispatch import receiver

try:
    from django.channels import Channel
except ImportError:
    from channels import Channel

from .models import VM, GazonEntry

stratus_app = apps.get_app_config('stratus')
signals = stratus_app.module.signals


@receiver(signals.before_action)
def alter_actionlist(sender, **kwargs):
    create_list = kwargs.get('create_list')
    delete_list = kwargs.get('delete_list')
    start_list = kwargs.get('start_list')
    stop_list = kwargs.get('stop_list')
    extend_list = []
    for n, vm in enumerate(create_list):
        try:
            gazon = vm.gazonentry
        except GazonEntry.DoesNotExist:
            pass
        else:
            create_list.remove(vm)
    for n, vm in enumerate(delete_list):
        try:
            gazon = vm.gazonentry
        except GazonEntry.DoesNotExist:
            pass
        else:
            delete_list.remove(vm)

@receiver(signals.vm_created)
def vm_created(sender, **kwargs):
    vm = kwargs.get('vm')
    try:
        gazon = vm.gazonentry
    except GazonEntry.DoesNotExist:
        gazon = GazonEntry.objects.create(vm=vm, gazon_status='WAITING')
    gazon.gazon_status='WAITING'
    vm.IP = None
    vm.status = 'TO_CREATE'

@receiver(signals.vm_deleted)
def vm_deleted(sender, **kwargs):
    vm = kwargs.get('vm')
    try:
        gazon = vm.gazonentry
    except GazonEntry.DoesNotExist:
        pass
    else:
        gazon.delete_vm()
