
from __future__ import absolute_import, unicode_literals

from rest_framework import serializers
from .models import VM, GazonEntry

class GazonEntryListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = GazonEntry
        fields = ('gazon_status', 'gazon_error', 'vm')

class GazonEntrySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = GazonEntry
        fields = ('gazon_status', 'gazon_error')
        read_only_fields = ('vm')


class GazonPostSerializer(serializers.Serializer):

    IP = serializers.IPAddressField()
