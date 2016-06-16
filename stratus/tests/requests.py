from django.test import TestCase
from ..models import VM
from django.test import Client

class CreateVM(TestCase):
    def setUp(self):
        VM.objects.create(name='pipo.vm')

    def test_create_conflict(self):
        """Try to create an already existing vm"""
	c = Client()
        response = c.post('/v1/vms',
	    {'hkvm': None,
	     'args': '-n pipo.vm -m 4096 --disk :10248'})
        self.assertEqual(response.status_code, 400)
	self.assertEqual(len(VM.objects.filter(name='pipo.vm')), 1)

    def test_create_no_conflict(self):
        """Try to create an already existing vm"""
	c = Client()
        response = c.post('/v1/vms',
	    {'hkvm': None,
	     'args': '-n pipo2.vm -m 4096 --disk :10248'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(VM.objects.filter(name='pipo.vm')), 2)

