from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.utils.module_loading import import_string

try:
    from django.channels.routing import route
except ImportError:
    from channels.routing import route

from .consumers import gazon_worker


channel_routing = [
    route(u'gazonentry', gazon_worker),
]
