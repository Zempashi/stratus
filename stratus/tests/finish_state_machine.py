from django.test import TestCase
from ..models import VM

class CreateVM(TestCase):
    def setUp(self):
        VM.objects.create(name='pipo')
