from django.test import Client
try:
    from django.channels.tests import ChannelTestCase
except ImportError:
    from channels.tests import ChannelTestCase

from stratus.consumers import VMConsumer

class TestManager(ChannelTestCase):

    def test_create(self):
        c = Client()
        response = c.post('/v1/vms',
            {'args': '-n pipo.vm -m 4096 --disk :10248'})
        VMConsumer(manager_module='stratus.managers.testmanager.manager.TestManager').create_vms(
            self.get_next_message('create-vms', require=True))
        self.assertTrue(True)
