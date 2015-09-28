from klein import Klein
from twisted.internet import reactor

from . import event
from . import validate
from . import constants
from . import label

app = Klein()



@app.route('/github', methods=['POST'])
def gh_events(request):
    event_name = request.getHeader(constants.GITHUB_API_HEADER_EVENT)
    handler = event.github.handler.get(event_name)
    if not handler:
        return "GitHub event `{0}` is not of interest.".format(event_name)
    payload = validate.payload(request)
    handler_instance = handler(payload)
    reactor.callLater(1, handler_instance)
    return 'Thanks for that'


def bb_handle(packet):
    'Handle Buildbot event'
    handler = event.buildbot.handler.get(packet['event'])
    if not handler:
        return "Buildbot event `{0}` not of interest.".format(event_name)
    payload = validate.payload(request)
    handler_instance = handler(payload)
    reactor.callLater(1, handler_instance)


@app.route('/buildbot', methods=['POST'])
def bb_events(request):
    packets = json.loads(request.args['packets'])
    if isinstance(packets, list):
        for packet in packets:
            bb_handle(packet)
    return 'Thanks for that'


def main(port):
    print('Setting up labels ...')
    label.init()
    app.run("localhost", port)
