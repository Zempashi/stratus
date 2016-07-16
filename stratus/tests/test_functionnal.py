from __future__ import absolute_import, unicode_literals

from django.test import TransactionTestCase, Client
from django.test import override_settings, modify_settings

try:
    from django.channels.tests import ChannelTestCase
except ImportError:
    from channels.tests import ChannelTestCase

from stratus.consumers import get_consumer
class TestManager(ChannelTestCase, TransactionTestCase):
    available_apps = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'channels',
        'rest_framework',
        'stratus',
    ]

    @override_settings(STRATUS_MANAGER=
            'stratus.managers.testmanager.manager.TestManager')
    def test_create(self):
        c = Client()
        response = c.post('/v1/vms',
             {'args': '-n pipo.vm -m 4096 --disk :10248'})
        get_consumer().create_vms(self.get_next_message(u'create-vms', require=True))
        self.assertTrue(True)
