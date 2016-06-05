from django.conf import settings

STRATUS_MANAGER = getattr(settings, 'STRATUS_MANAGER', "stratus.managers.aknansible.manager.AknAnsibleManager")
STRATUS_ALLOCATOR = getattr(settings, 'STRATUS_ALLOCATOR', "stratus.allocators.hkvmallocator.allocator.HKVMAllocator")
