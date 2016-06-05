from channels.routing import route, include

from stratus import routing as stratus_routing

channel_routing = [
    include(stratus_routing.channel_routing)
]
