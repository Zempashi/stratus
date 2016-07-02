
from rest_framework import serializers

from .models import HKVM, HKVMGroup


class HKVMSerializer(serializers.HyperlinkedModelSerializer):

    last_status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)

    class Meta:
        model = HKVM
        fields = ('id', 'name', 'virtual', 'last_status', 'last_updated', 'created', 'vm_set', 'url')


class HKVMGroupSerializer(serializers.ModelSerializer):

    hkvms = serializers.HyperlinkedRelatedField(view_name='hkvm-detail', queryset=HKVM.objects.all(), many=True)

    class Meta:
        model = HKVMGroup
