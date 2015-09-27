from klein import Klein
from twisted.internet import reactor

from . import event
from . import validate

app = Klein()


def handle_request(request):
    event_name = request.getHeader('X-Github-Event')
    handler = event.handler.get(event_name)
    if not handler:
        return "GitHub event `{0}` is not supported".format(event_name)
    payload = validate.payload(request)
    handler_instance = handler(payload)
    reactor.callLater(1, handler_instance)


@app.route('/', methods=['POST'])
def gh_events(request):
    handle_request(request)
    return 'Thanks for that'


def main(port):
    app.run("localhost", port)
