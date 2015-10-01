# coding: utf-8
import re
from .. import github
from .. import config

RE_CMD = re.compile("@{0} (?P<cmd>[\w]+) ?(?P<arg>[\w/]+)?".format(config.github_user))


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
        number = self.payload['issue']['number']
        commenter = self.payload['comment']['user']['login']
        match = RE_CMD.match(self.payload['comment']['body'])
        if not match:
            return
        cmd = match.group('cmd')
        method = getattr(self, "_{0}".format(cmd), None)
        if not method:
            repo = self.payload['repository']['full_name']
            comment_resp = github.sync_post(
                "repos/{0}/issues/{1}/comments".format(repo, number),
                json={'body': "@{0} :pear: `{1}`?".format(commenter, cmd)}
            )
            assert comment_resp.ok
            return
        method(commenter, match.group('arg'))

    def _try(self, user, suite):
        'Run the [requested] test suite'
        if user not in config.developers and user not in config.mergers:
            return
        if not suite:
            suite = 'bmu'
        import ipdb;ipdb.set_trace()

    def _merge(self, user, suite):
        'Run all test suites, and merge if successful'
        if user not in config.mergers:
            return


handler = {
    'ping': Ping,
    'issue_comment': IssueComment,
}
