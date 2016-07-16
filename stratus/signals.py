
from __future__ import absolute_import, unicode_literals

import django.dispatch

vm_allocated = django.dispatch.Signal(providing_args=['vm'])
vm_to_create = django.dispatch.Signal(providing_args=['vm'])
vm_created = django.dispatch.Signal(providing_args=['vm'])
vm_deleted = django.dispatch.Signal(providing_args=['vm'])
vm_start = django.dispatch.Signal(providing_args=['vm'])
vm_stop = django.dispatch.Signal(providing_args=['vm'])
vm_update = django.dispatch.Signal(providing_args=['serializer'])

before_action = django.dispatch.Signal(providing_args=['create_list', 'delete_list'])
#after_allocation = django.displatch.Signal(providind_args=['vm_to_hkvm_map'])

#vm_before_action = django.displatch.Signal(providind_args=['vm', 'hkvm'])
