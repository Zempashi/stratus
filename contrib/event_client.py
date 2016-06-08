import os
try:
    from autobahn.asyncio.websocket import WebSocketClientProtocol, \
                WebSocketClientFactory
    AUTOBAHN='asyncio'
except ImportError:
    from autobahn.twisted.websocket import WebSocketClientProtocol, \
                WebSocketClientFactory
    AUTOBAHN='twisted'

class DebugClientProtocol(WebSocketClientProtocol):

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {} bytes".format(len(payload)))
        else:
            print("Text message received: {}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {}".format(reason))

def twisted_start():

    import sys

    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)
    url = os.environ.get('STRATUS_URL', u"ws://127.0.0.1:9000")
    scheme, url_start, port = url.split(':')
    _, _, ip = url_start.split('/')

    factory = WebSocketClientFactory(url)
    factory.protocol = DebugClientProtocol

    reactor.connectTCP(ip, int(port), factory)
    reactor.run()


def asyncio_start():
    import asyncio
    url = os.environ.get('STRATUS_URL', u"ws://127.0.0.1:9000")
    scheme, url_start, port = url.split(':')
    _, _, ip = url_start.split('/')

    factory = WebSocketClientFactory(url)
    factory.protocol = DebugClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, ip, int(port))
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()

d = {'twisted': twisted_start, 'asyncio': asyncio_start}
d[AUTOBAHN]()
