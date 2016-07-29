
from __future__ import absolute_import, unicode_literals

import logging


from django.utils import six
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings

from arkena_api_gazon_client.gazon_requestor import GazonRequestor

from .models import GazonEntry

class GazonEntryPlugin(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        gazon_settings = settings.STRATUS_GAZON_ENTRY
        gazon_zones = gazon_settings['zones']
        global_config = gazon_zones.get('GLOBAL', {})
        self._gazon_requestor = {}
        for zone, zone_conf in six.iteritems(gazon_zones):
            conf = global_config.copy()
            conf.update(zone_conf)
            user = conf.get('USER', None)
            password = conf.get('PASS', None)
            if user or password:
                auth = (user, password)
            else:
                auth = None
            gazon_requestor = GazonRequestor(
                host=conf['HOST'],
                port=conf.get('PORT', 1027),
                zone=zone,
                namespace=conf.get('NAMESPACE', 'arkena'),
                auth=auth,
                verifySSL="True" if conf.get('VERIFY_SSL', True) else False,
            )
            self._gazon_requestor[zone] = gazon_requestor

    def make_entry(self):
        new_entry = GazonEntry.objects.filter(gazon_status='TO_CREATE',
                                              gazon_error='')
        for entry in new_entry:
            vm = entry.vm
            name = vm.name
            IP = vm.IP
            if not IP:
                raise ValueError('GazonEntry for a VM that have no IP')
            zone = self.find_zone_entry(name)
            gr = self._gazon_requestor[zone]
            if self.find_single_record(gr, name):
                gr.updateRecord(name, 'A', entry.vm.IP)
            else:
                gr.addRecord('A', name, entry.vm.IP)
            vm.status = 'STARTED'
            vm.save()

    def delete_entry(self):
        del_entry = GazonEntry.objects.filter(gazon_status='TO_DELETE',
                                              gazon_error='')
        for entry in del_entry:
            vm = entry.vm
            name = vm.name
            zone = self.find_zone_entry(name)
            gr = self._gazon_requestor[zone]
            record = self.find_single_record(gr, name)
            if record:
                gr.delRecordof(name)
            # else: No record found, that's what wanted
            vm.status = 'DELETED'
            vm.save()

    def find_single_record(self, requestor, name):
        all_record = requestor._GazonRequestor__findAllRecord(name, False)
        if all_record:
            if len(all_record) > 1:
                raise ValueError('Too many record to for \'{}\' '
                                 'It should have only one record, please'
                                 'fix manually. Aborting.'.format(name))
            else:
                return all_record[0]
        else:
            return None

    def find_zone_entry(self, entry):
        for zone in six.iterkeys(self._gazon_requestor):
            if zone in entry:
                return zone
        else:
            raise ValueError('Entry doesn\'t match any zone')


def gazon_worker(message, **kwargs):
    gep = GazonEntryPlugin()
    gep.make_entry()
    gep.delete_entry()
