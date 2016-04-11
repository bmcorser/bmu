import json

from klein import Klein
from twisted.internet import reactor

from .event import github as github_event
from .event import buildbot as buildbot_event
from . import validate
from . import constants
from . import label

app = Klein()



@app.route('/github', methods=['POST'])
def gh_events(request):
    event_name = request.getHeader(constants.GITHUB_API_HEADER_EVENT)
    # print("Received `{0}` from GitHub".format(event_name))
    handler = github_event.handler.get(event_name)
    if not handler:
        print("GitHub event `{0}` is not of interest.".format(event_name))
        return
    payload = validate.payload(request)
    handler_instance = handler(payload)
    reactor.callLater(1, handler_instance)
    return 'Thanks for that'


def bb_handle(packet):
    'Handle Buildbot event'
    event_name = packet['event']
    # print("Received `{0}` from Buildbot".format(event_name))
    handler = buildbot_event.handler.get(event_name)
    if not handler:
        # print("Buildbot event `{0}` is not of interest.".format(event_name))
        return
    try:
        handler_instance = handler(packet['payload'])
        reactor.callLater(1, handler_instance)
    except KeyError as exc:
        builder = packet['payload']['build']['builderName']
        print("Builder {0} not supported".format(builder))


@app.route('/buildbot', methods=['POST'])
def bb_events(request):
    for packets in request.args['packets']:
        map(bb_handle, json.loads(packets))
    return 'Thanks for that'


def main(port):
    print('Setting up labels ...')
    label.init()
    app.run("localhost", port)
