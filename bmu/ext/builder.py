import json
import sys

from buildbot.plugins import util, steps
from twisted.internet import defer


def getChanges(request, options=None):
    bmu_payload = json.loads(request.content.read())
    return bmu_payload, 'git'


def inject(buildbot_module):
    setattr(buildbot_module.status.web.hooks, 'bmu', sys.modules[__name__])


class GitHubTrigger(steps.Trigger):

    def __init__(self, defaultSchedulers):
        'Call parent __init__ with a truthy placeholder for schedulerNames'
        self.defaultSchedulers = defaultSchedulers
        steps.Trigger.__init__(
            self, schedulerNames=True,
            waitForFinish=True,
            updateSourceStamp=True
        )

    @defer.inlineCallbacks
    def start(self):
        'Set schedulers based on labels, default to trigger-pr-runner'
        # TODO: Grab all the other relevant things
        schedulers = self.getProperty('schedulers')
        if schedulers:
            self.schedulerNames = schedulers
        else:
            self.schedulerNames = self.defaultSchedulers
        yield steps.Trigger.start(self)


def bmu_builder(name, slavenames, defaultSchedulers):
    bmu_f = util.BuildFactory()
    bmu_f.addStep(GitHubTrigger(defaultSchedulers=defaultSchedulers))
    return util.BuilderConfig(name=name,
                              slavenames=slavenames,
                              factory=bmu_f)
