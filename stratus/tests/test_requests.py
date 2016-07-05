from django.test import TestCase
from ..models import VM
from django.test import Client

class CreateVM(TestCase):
    def setUp(self):
        VM.objects.create(name='pipo.vm')

    def test_create_conflict(self):
        """Try to create an already existing vm and failing"""
	c = Client()
        response = c.post('/v1/vms',
	    {'args': '-n pipo.vm -m 4096 --disk :10248'})
        self.assertEqual(response.status_code, 400)
	self.assertEqual(len(VM.objects.all()), 1)

    def test_create_no_conflict(self):
        """Try to create an already existing vm and succeeding"""
	c = Client()
        response = c.post('/v1/vms',
	    {'args': '-n pipo2.vm -m 4096 --disk :10248'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(VM.objects.all()), 2)
