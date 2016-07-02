
from __future__ import absolute_import

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

try:
    from django.channels import Channel
except ImportError:
    from channels import Channel

from .vms.views import VMList, VMDetail
from .hkvms.views import HKVMList, HKVMDetail, HKVMGroupList

@api_view(['GET'])
def api_root(request, version):
    if version == 'v1':
        return Response({'vms': reverse('v1:vm-list', args=(), request=request),
                         'hkvms': reverse('v1:hkvm-list', args=(), request=request)})
    else:
        return Response({'api_root': reverse(api_root, kwargs={'version': 'v1'}, request=request)})


@api_view(['GET'])
def run_worker(request):
    Channel('create-vms').send(dict())
    return Response({'message_send': True})
