from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.utils.module_loading import import_string

try:
    from django.channels.routing import route
except ImportError:
    from channels.routing import route

#from .consumers import ws_add, ws_message, ws_disconnect
from .consumers import get_consumer

vm_consumer = get_consumer()

channel_routing = [
#    route("websocket.connect", ws_add),
#    route("websocket.receive", ws_message),
#    route("websocket.disconnect", ws_disconnect),
    route(u'create-vms', vm_consumer.create_vms),
]

for app in apps.get_app_configs():
    try:
        stratus_include_routing = app.stratus_include_routings
    except AttributeError:
        pass
    else:
        if stratus_include_routing:
            routing = import_string(app.name + '.routing.channel_routing')
            channel_routing.extend(routing)

