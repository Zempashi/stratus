from rest_framework import serializers
from .models import VM, VM_STATUS_ENUM
from .models import HKVM, HKVM_STATUS_ENUM

class VMSerializer(serializers.HyperlinkedModelSerializer):

    status = serializers.CharField(read_only=True)

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'url')
        extra_kwargs = {
            'hkvm':  {'view_name': 'hkvm-detail'}
        }


class VMDetailSerializer(serializers.HyperlinkedModelSerializer):

    status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'created', 'url')
        extra_kwargs = {
            'hkvm':  {'view_name': 'hkvm-detail'}
        }

class HKVMSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = HKVM
        fields = ('id', 'name', 'last_status', 'url')

class HKVMDetailSerializer(serializers.HyperlinkedModelSerializer):

    last_status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)

    class Meta:
        model = HKVM
        fields = ('id', 'name', 'last_status', 'last_status_updated', 'created', 'vm_set', 'url')
