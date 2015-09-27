import requests
from bmu import constants

class BaseEvent(object):

    def __init__(self, payload):
        self.payload = payload


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
            labels = requests.get(self.pr_dict['issue_url'], auth=('bmcorser', constants.GITHUB_TOKEN)).json()['labels']
        else:
            'Where do the labels appear?'
            import ipdb;ipdb.set_trace()
        self.build()

    def build(self):
        repo = self.payload['repository']['full_name']
        commit = self.pr_dict['merge_commit_sha']
        branch = self.pr_dict['head']['ref']
        is_mergeable = self.pr_dict['mergeable_state'] == 'clean'
        pr_number = self.pr_dict['number']

class IssueComment(BaseEvent):

    def __call__(self):
        pass

handlers = {
    'pull_request': PullRequest,
    'ping': Ping,
    'issue_comment': IssueComment,
}
