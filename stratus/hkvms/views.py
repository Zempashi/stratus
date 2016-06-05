
from django.shortcuts import render

from .models import HKVM
from .serializers import HKVMSerializer
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


class HKVMList(mixins.ListModelMixin,
             generics.GenericAPIView):
    """
    List all VM, or create a new one.
    """

    queryset = HKVM.objects.all()
    serializer_class = HKVMSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, format=None):
        serializer = HKVMSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            if not serializer.validated_data['name']:
                hkvm = serializer.save(status='INCOMPLETE')
            else:
                hkvm = serializer.save(status='UNKNOWN')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HKVMDetail(mixins.RetrieveModelMixin,
                generics.GenericAPIView):
    """
    Retrieve, update or delete a snippet instance.
    """

    queryset = HKVM.objects.all()
    serializer_class = HKVMSerializer

    def _get_object(self, pk):
        try:
            return HKVM.objects.get(pk=pk)
        except HKVM.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, pk, format=None):
        hkvm = self._get_object(pk)
        serializer = HKVMSerializer(hkvm, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        hkvm = self._get_object(pk)
        hkvm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

