import json

import treq
from klein import Klein

from . import events

app = Klein()


@app.route('/', methods=['POST'])
def gh_events(request):
    # import ipdb;ipdb.set_trace()
    event_name = request.headers.get('X-Github-Event')
    payload = json.load(request.content)
    # d = treq.get('https://www.google.com' + request.uri)
    # d.addCallback(treq.content)
    # return d

def main(port):
    app.run("localhost", port)
