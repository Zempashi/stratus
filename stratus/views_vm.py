from django.shortcuts import render

# Create your views here.

from .models import VM
from .serializers import VMSerializer, VMDetailSerializer
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

class VMList(mixins.ListModelMixin,
             generics.GenericAPIView):
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
            if not serializer.validated_data['name']:
                vm = serializer.save(status='INCOMPLETE')
            else:
                vm = serializer.save(status='UNKNOWN')
            Channel('create-vms').send(dict())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VMDetail(mixins.RetrieveModelMixin,
               generics.GenericAPIView):
    """
    Retrieve, update or delete a snippet instance.
    """

    queryset = VM.objects.all()
    serializer_class = VMDetailSerializer

    def _get_object(self, pk):
        try:
            return VM.objects.get(pk=pk)
        except VM.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, pk, format=None):
        vm = self._get_object(pk)
        serializer = VMDetailSerializer(vm, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        vm = self._get_object(pk)
        vm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
