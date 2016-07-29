from django.apps import AppConfig

class GazonEntryConfig(AppConfig):
    name = 'stratus_plugins.gazonentry'
    verbose_name = 'Make Gazon Entry for VM'


    stratus_include_url = True
    stratus_include_routings = True

    def ready(self):
        from . import signals
