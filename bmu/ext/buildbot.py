import json
import sys


def getChanges(request, options=None):
    """
    Responds only to POST events and starts the build process

    :arguments:
        request
            the htp request object
    """
    bmu_payload = json.loads(request.content.read())
    return bmu_payload, 'git'


def inject(buildbot_module):
    setattr(buildbot_module.status.web.hooks, 'bmu', sys.modules[__name__])
