# coding: utf-8
import re
from .. import github
from .. import config

RE_CMD = re.compile("@{0} (?P<cmd>[\w]+) ?(?P<arg>[\w/, ]+)?".format(config.github_user))


class BaseGitHubEvent(object):

    def __init__(self, payload):
        self.payload = payload


class Ping(BaseGitHubEvent):

    def __call__(self):
        return


class IssueComment(BaseGitHubEvent):

    def __call__(self):
        if 'pull_request' not in self.payload['issue']:
            # This isn’t a comment on a PR
            return
        repo = self.payload['repository']['full_name']
        number = self.payload['issue']['number']
        commenter = self.payload['comment']['user']['login']
        match = RE_CMD.match(self.payload['comment']['body'])
        if not match:
            return
        cmd = match.group('cmd')
        method = getattr(self, "_{0}".format(cmd), None)
        if not method:
            comment_resp = github.sync_post(
                "repos/{0}/issues/{1}/comments".format(repo, number),
                json={'body': "@{0} :pear: `{1}`?".format(commenter, cmd)}
            )
            assert comment_resp.ok
            return
        method(repo, number, commenter, match.group('arg'))

    def _try(self, repo, number, user, suites):
        'Run the [requested] test suite'
        if not suites:
            suites = [config.namespace]
        suites = map(lambda string: string.strip(','), suites.split())
        if user not in config.developers and user not in config.mergers:
            return

    def _merge(self, user, suite):
        'Run all test suites, and merge if successful'
        if user not in config.mergers:
            return


class PullRequest(BaseGitHubEvent):

    def __init__(self, *args, **kwargs):
        super(PullRequest, self).__init__(*args, **kwargs)
        self.handlers = {
            'labeled': self._labeled,
            'unlabeled': self._unlabeled,
        }

    def __call__(self):
        print('Ok PR')
        action = self.payload.get('action')
        if not action:
            raise Exception('No action took place?')
        handler = self.handlers.get(action)
        if not handler:
            print("Action not handled: {0}".format(action))
        handler()

    def _labeled(self):
        print("{0} -> {1}".format(label['name']))

    def _unlabeled(self):
        label = self.payload['label']
        print("Removed label: {0}".format(label['name']))

class LabellingEvent(object):

    def __init__(self, payload):
        self.labels = [self.payload['label']]
        self.repo = self.payload['repository']['full_name']
        self.number = self.payload['repository']['full_name']


handler = {
    'ping': Ping,
    'issue_comment': IssueComment,
    'pull_request': PullRequest,
}
