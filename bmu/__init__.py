import json

import treq
from klein import Klein
from twisted.internet import reactor, defer

from . import events
from .validate import validate_request

app = Klein()


def handle_request(request):
    event_name = request.getHeader('X-Github-Event')
    if event_name == 'ping':
        return
    event_handler = getattr(events, event_name, None)
    if not event_handler:
        return "GitHub event `{0}` is not supported".format(event_name)
    # validate_request(request)
    d = defer.Deferred()
    d.addCallback(event_handler)
    try:
        payload = json.load(request.content)
    except:
        raise Exception('Could not parse JSON from request')
    reactor.callLater(1, d.callback, payload)

@app.route('/', methods=['POST'])
def gh_events(request):
    handle_request(request)
    return 'Thanks for that'


def main(port):
    app.run("localhost", port)
