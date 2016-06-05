from django.db import models

# Create your models here.

VM_STATUS_ENUM = [  ('UNKNOWN',  'VM status is unknown'),
                    ('CREATION', 'VM is currently created'),
                    ('CREATED',  'VM has been created'),
                    ('STOPPED',  'VM is stopped'),
                    ('STARTED',  'VM is currently running'),
                    ('VANISHED', 'VM has disappeared without stratus action'),
                    ('DELETED',  'VM has been deleted'),
                    ('INCOMPLETE', 'VM status is incomplete'),
                    ('CREATION_FAILURE', 'VM has failed being created'),
                ]

HKVM_STATUS_ENUM = [('UNKNOWN',  'HKVM status is unknown'),
                    ('OK',       'HKVM is running'),
                    ('FAILURE',  'HKVM has failed'),
                ]

class VM(models.Model):
    name = models.CharField(max_length=100)
    hkvm = models.ForeignKey('HKVM', null=True, on_delete=models.SET_NULL)
    args = models.TextField()
    status = models.CharField(choices=VM_STATUS_ENUM, default='UNKNOWN', max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created',)


class HKVM(models.Model):
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True, null=True)
    last_status = models.CharField(choices=HKVM_STATUS_ENUM, default='UNKNOWN', max_length=100)
