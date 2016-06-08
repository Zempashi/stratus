
from __future__ import absolute_import

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

from .vms.views import VMList, VMDetail
from .hkvms.views import HKVMList, HKVMDetail

@api_view(['GET'])
def api_root(request, version):
    if version == 'v1':
        return Response({'vms': reverse('v1:vm-list', args=(), request=request),
                         'hkvms': reverse('v1:hkvm-list', args=(), request=request)})
    else:
        return Response({'api_root': reverse(api_root, kwargs={'version': 'v1'}, request=request)})
