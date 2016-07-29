
from __future__ import absolute_import, unicode_literals

from rest_framework import mixins
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework import renderers
from rest_framework.decorators import api_view

try:
    from django.channels import Channel
except ImportError:
    from channels import Channel

from .models import VM, GazonEntry
from .serializers import GazonEntrySerializer,\
                         GazonEntryListSerializer,\
                         GazonPostSerializer

class GazonEntryList(mixins.ListModelMixin, generics.GenericAPIView):
    """
    List all gazon entry
    """

    queryset = GazonEntry.objects.all()
    serializer_class = GazonEntryListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)



class GazonEntryDHCP(mixins.CreateModelMixin,
                     generics.RetrieveAPIView):

    queryset = GazonEntry.objects.all()
    serializer_class = GazonPostSerializer

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            int(pk)
	    self.queryset = VM.objects.all()
        except ValueError:
            self.kwargs['name'] = pk
            self.lookup_field = 'name'
            self.queryset = VM.objects.exclude(status__in=['PENDING', 'DELETED']).all()
        vm = super(GazonEntryDetail, self).get_object()
        try:
	    return vm.gazonentry
        except GazonEntry.DoesNotExist as exc:
            exc.from_vm = vm
            raise

    def post(self, request, *args, **kwargs):
        context = {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self }
        gazon_post = GazonPostSerializer(data=request.data, context=context)
        gazon_post.is_valid(raise_exception=True)
        try:
            gazonentry = self.get_object()
        except GazonEntry.DoesNotExist as exc:
            vm = exc.from_vm
            GazonEntry.objects.create(vm = vm, gazon_status='TO_CREATE')
        else:
            vm = gazonentry.vm
            gazonentry.gazon_status = 'TO_CREATE'
            gazonentry.save()

        vm.IP = gazon_post.validated_data['IP']
        vm.save()
        Channel(u'gazonentry').send(dict())
        headers = self.get_success_headers(gazon_post.data)
        return Response(gazon_post.data, status=status.HTTP_201_CREATED, headers=headers)

class GazonEntryDetail(mixins.CreateModelMixin,
                       generics.RetrieveAPIView,
                       generics.DestroyAPIView):
    """
    Retrieve, update or delete a GazonEntryVM
    """

    queryset = GazonEntry.objects.all()
    serializer_class = GazonEntrySerializer

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            int(pk)
	    self.queryset = VM.objects.all()
        except ValueError:
            self.kwargs['name'] = pk
            self.lookup_field = 'name'
            self.queryset = VM.objects.exclude(status__in=['PENDING', 'DELETED']).all()
        vm = super(GazonEntryDetail, self).get_object()
        try:
	    return vm.gazonentry
        except GazonEntry.DoesNotExist as exc:
            exc.from_vm = vm
            raise

@api_view(['GET'])
def run_worker(request):
    Channel(u'gazonentry').send(dict())
    return Response({'message_send': True})
