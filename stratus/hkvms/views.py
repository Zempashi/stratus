
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
    List all HKVM, or create a new one.
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


class HKVMDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an HKVM
    """

    queryset = HKVM.objects.all()
    serializer_class = HKVMSerializer

    def get_serializer_class(self):
	if self.kwargs.get('full', False):
	    return HKVMSerializer
	else:
	    return HKVMSerializer
