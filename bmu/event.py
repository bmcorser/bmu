from twisted.internet import defer, reactor
from . import github


class BaseEvent(object):

    def __init__(self, payload):
        self.payload = payload
        self.deferred = defer.Deferred()


class Ping(BaseEvent):

    def __call__(self):
        return


class PullRequest(BaseEvent):

    build_actions = (
        'labeled',
        'unlabeled',
        'opened',
        'reopened',
        'synchronize',
    )

    def __init__(self, payload):
        self.pr_dict = payload['pull_request']
        super(PullRequest, self).__init__(payload)

    def __call__(self):
        action = payload['action']
        if action not in self.build_actions:
            return
        if 'label' not in action:
            labels = github.get(self.pr_dict['issue_url'])
            labels.addCallback(github.key('labels'))
        else:
            'Where do the labels appear?'
            import ipdb;ipdb.set_trace()
        self.deferred.addCallback(self.build)
        reactor.callLater(0, self.deferred.callback(labels))

    def build(self, labels):
        repo = self.payload['repository']['full_name']
        commit = self.pr_dict['merge_commit_sha']
        branch = self.pr_dict['head']['ref']
        is_mergeable = self.pr_dict['mergeable_state'] == 'clean'
        pr_number = self.pr_dict['number']

class IssueComment(BaseEvent):

    def __call__(self):
        pass

handler = {
    'pull_request': PullRequest,
    'ping': Ping,
    'issue_comment': IssueComment,
}
