from django.shortcuts import render

from .models import VM
from .serializers import VMSerializer, \
                         VMDetailSerializer, \
                         VMFullSerializer
from ..signals import vm_update
from django.http import Http404
from rest_framework import mixins
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework import renderers

try:
    from django.channels import Channel
except ImportError:
    from channels import Channel


class VMList(mixins.ListModelMixin, generics.GenericAPIView):
    """
    List all VM, or create a new one.
    """

    queryset = VM.objects.all()
    serializer_class = VMSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, format=None):
        serializer = VMSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            vm = serializer.save(status='PENDING')
            Channel('create-vms').send(dict())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VMDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a VM.
    """

    queryset = VM.objects.all()

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            int(pk)
        except ValueError:
            self.kwargs['name'] = pk
            self.lookup_field = 'name'
            self.queryset = self.queryset.exclude(status__in=['PENDING', 'DELETED'])
        return super(VMDetail, self).get_object()

    def get_serializer_class(self):
        if self.kwargs.get('full', False):
            return VMFullSerializer
        else:
            return VMDetailSerializer

    def perform_destroy(self, vm):
        if vm.status in ['PENDING', 'DELETED', 'VANISHED']:
            vm.erase()
        else:
            vm.erase()
            vm.save()
            if vm.status == 'TO_DELETE':
                Channel('create-vms').send(dict())

    def perform_update(self, serializer):
        vm_update.send(sender=self.__class__, serializer=serializer)
        serializer.save()
