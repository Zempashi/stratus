from rest_framework import serializers
from .models import VM, VM_STATUS_ENUM
from .models import HKVM, HKVM_STATUS_ENUM

class VMSerializer(serializers.ModelSerializer):

    status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'created')


class HKVMSerialiser(serializers.ModelSerializer):

    status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'created')
