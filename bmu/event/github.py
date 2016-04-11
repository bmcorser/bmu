# coding: utf-8
import functools
import re
import operator
import urlparse
import urllib

import requests
import grequests

from .. import github
from .. import config
from .. import label

RE_CMD = re.compile("@{0} (?P<cmd>[\w]+) ?(?P<arg>[\w/, ]+)?".format(config.github_user))

BUILDS = {}  # One day, redis here


def bb_url(path):
    return urlparse.urljoin(config.buildbot_url, path)


def get_bb_builder_names():
    resp = requests.get(bb_url('json/builders'))
    return resp.json().keys()

strip_ns = lambda label: label.replace("{0}/".format(config.namespace), '')

def labels_to_suites(labels):
    suites = filter(lambda label: label.startswith(config.namespace), labels)
    if not suites:
        return [config.namespace]
    return map(strip_ns, suites)



class BaseGitHubEvent(object):

    def __init__(self, payload):
        self.payload = payload

    def start_builder(self, suite, name):
        print("Starting build for {0}, builder is {1}".format(suite, name))
        kwargs = {
            'data': {
                'forcescheduler': name,
                'revision': self.merge_commit,
                'property1_name': 'suite',
                'property1_value': suite,
                'property2_name': 'repo',
                'property2_value': self.repo,
                'property3_name': 'head_commit',
                'property3_value': self.head_commit,
                'property4_name': 'github_pr_number',
                'property4_value': self.number,
                # 'branch': '+refs/pull/*/merge:refs/remotes/origin/pr/*/merge',
                'branch': "refs/pull/{0}/merge".format(self.number),
            },
            'auth': tuple(config.buildbot_auth),
        }
        path = "builders/{0}/force".format(urllib.quote_plus(name))
        return grequests.post(bb_url(path), **kwargs)



class Ping(BaseGitHubEvent):

    def __call__(self):
        return


class IssueComment(BaseGitHubEvent):

    def __call__(self):
        if 'pull_request' not in self.payload['issue']:
            # This isn’t a comment on a PR
            return
        self.repo = self.payload['repository']['full_name']
        self.number = self.payload['issue']['number']
        self.user = self.payload['comment']['user']['login']
        comment_id = self.payload['comment']['id']
        pr_url = "repos/{0}/pulls/{1}".format(self.repo, self.number)
        pr_json = github.sync_get(pr_url).json()
        self.merge_commit = pr_json['merge_commit_sha']
        self.head_commit = pr_json['head']['sha']
        match = RE_CMD.match(self.payload['comment']['body'])
        if not match:
            return
        cmd = match.group('cmd')
        method = getattr(self, "_{0}".format(cmd), None)
        if not method:
            comment_resp = github.sync_post(
                "repos/{0}/issues/{1}/comments".format(self.repo, self.number),
                json={'body': "@{0} :pear: `{1}`?".format(self.user, cmd)}
            )
            assert comment_resp.ok
            return
        delete_resp = github.sync_delete(
            "repos/{0}/issues/comments/{2}".format(
                self.repo,
                self.number,
                comment_id
            )
        )
        method(match.group('arg'))

    def suite_to_builders(self, suite, all_builders):
        all_suites = map(strip_ns, label.get_configured_labels(self.repo))
        if suite == config.namespace:
            return set(all_suites).intersection(all_builders)
        builders = []
        for builder in all_builders:
            if builder.startswith(suite) and builder in all_suites:
                builders.append(builder)
        return builders

    def _try(self, suites):
        'Run the [requested] test suite(s)'
        if self.user not in config.developers and self.user not in config.mergers:
            return  # maybe should talk bak you're not allowed
        if not suites:  # refer to labels
            suites = labels_to_suites(map(operator.itemgetter('name'), self.payload['issue']['labels']))
        else:  # specific label requested
            suites = labels_to_suites(map(lambda string: string.strip(','), suites.split()))
        all_builders = get_bb_builder_names()
        BUILDS[self.merge_commit] = {}
        for suite in suites:
            BUILDS[self.merge_commit][suite] = {}
            builders = self.suite_to_builders(suite, all_builders)
            for builder in builders:
                BUILDS[self.merge_commit][suite][builder] = None
            grequests.map(map(functools.partial(self.start_builder, suite), builders))

    def _merge(self, *args):
        'Run all test suites, and merge if successful'
        if self.user not in config.mergers:
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
        label = self.payload['label']
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
