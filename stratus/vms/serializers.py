
from __future__ import absolute_import, unicode_literals

import argparse
import re

from django.utils import six

from rest_framework import serializers
from .models import VM


def _scientific_int(value):
    try:
        return float(value)
    except ValueError:
        res = re.match('(?P<num>\d+)\s*(?P<ext>[\w]*)', value)
        num = float(res.group('num'))
        ext = res.group('ext')
        mapping = {'G': 1, 'M': 0, 'K': -1}
        if ext:
            prefix = mapping[ext[0]]
        else:
            prefix = 0
        try:
            if ['o', 'B', 'i', ''].index(ext[1:]):
                return num*(1024**prefix)
        except ValueError:
            return num*(1024**prefix)/8.


class VMSerializer(serializers.HyperlinkedModelSerializer):

    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)
    memory = serializers.IntegerField(read_only=True)
    disk = serializers.IntegerField(read_only=True)
    error = serializers.CharField(read_only=True)

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'created', 'url',
                  'memory', 'disk', 'error')
        extra_kwargs = {
            'hkvm': {'view_name': 'hkvm-detail'}
        }

    def validate(self, data):
        data['name'], data['memory'], data['disk'] = \
            self._parse_install_system(data['args'])
        return data

    def _parse_install_system(self, command_line):
        parser = argparse.ArgumentParser()
        parser.add_argument('-n', dest='name')
        parser.add_argument('-m', '--memory')
        parser.add_argument('-d', '--disk', action='append')
        args, rest = parser.parse_known_args(command_line.split())
        print(args, rest)
        try:
            total_disk = 0
            for disk in args.disk:
                expr_disk = disk.split(':')
                try:
                    disk_size, = expr_disk
                except ValueError:
                    _, disk_size = expr_disk
                total_disk += _scientific_int(disk_size)
        except TypeError as exc:
            six.raise_from(ValueError('No disk specified'), exc)
        if args.memory is None:
            raise ValueError('No mem specified')
        else:
            memory = _scientific_int(args.memory)
        if args.name is None:
            raise ValueError('No name specified')
        else:
            name = args.name
        return name, memory, total_disk


class VMDetailSerializer(VMSerializer):

    def __init__(self, *args, **kwargs):
        super(VMSerializer, self).__init__(*args, **kwargs)

        if self.instance and not self.instance.status == 'PENDING':
            self.fields['args'].read_only = True
            self.fields['hkvm'].read_only = True


class VMFullSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = VM
        fields = ('id', 'name', 'hkvm', 'args', 'status', 'created', 'url',
                  'memory', 'disk', 'error')
        extra_kwargs = {
            'hkvm': {'view_name': 'hkvm-detail'}
        }
