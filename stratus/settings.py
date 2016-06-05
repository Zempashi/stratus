from django.conf import settings

STRATUS_MANAGER = getattr(settings, 'STRATUS_MANAGER', "stratus.managers.AknAnsible")
