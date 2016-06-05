from django.conf import settings

STRATUS_ANSIBLE_INVENTORY = getattr(settings, 'STRATUS_ANSIBLE_INVENTORY', None)

