from twisted.internet import defer, reactor
from . import github


class BaseGitHubEvent(object):

    def __init__(self, payload):
        self.payload = payload
        self.deferred = defer.Deferred()


class BaseBuildbotEvent(object):


class Ping(BaseGitHubEvent):

    def __call__(self):
        return


class PullRequest(BaseGitHubEvent):

    build_actions = (
        'labeled',
        'opened',
        'reopened',
        'synchronize',
    )

    def __init__(self, payload):
        pr_dict = payload['pull_request']
        self.repo = payload['repository']['full_name']
        self.merge_commit = pr_dict['merge_commit_sha']
        self.branch = pr_dict['head']['ref']
        self.number = pr_dict['number']
        self.pr_dict = pr_dict
        super(PullRequest, self).__init__(payload)

    def __call__(self):
        action = self.payload['action']
        print(action)
        if action not in self.build_actions:
            return
        if action == 'labeled':
            self.build([self.payload['label']])
            return
        labels = github.sync_get(self.pr_dict['issue_url']).json()['labels']
        self.build(labels)

    def build(self, labels):
        if not self.pr_dict['mergeable']:
            print("Not mergeable :(")
            return
        print("Building against labels: {0}".format(labels))


class IssueComment(BaseGitHubEvent):

    def __call__(self):
        body = self.payload['comment']['body']
        commenter = self.payload['comment']['user']['login']
        if commenter == config.github_user
        import ipdb;ipdb.set_trace()
        pass

handler = {
    'pull_request': PullRequest,
    'ping': Ping,
    'issue_comment': IssueComment,
}
