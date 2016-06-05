try:
    from django.channels.routing import route
except ImportError:
    from channels.routing import route

#from .consumers import ws_add, ws_message, ws_disconnect
from .consumers import vm_consumer

channel_routing = [
#    route("websocket.connect", ws_add),
#    route("websocket.receive", ws_message),
#    route("websocket.disconnect", ws_disconnect),
    route('create-vms', vm_consumer.create_vms),
]
