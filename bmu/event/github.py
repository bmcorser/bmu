from . import github
from . import config


class BaseGitHubEvent(object):

    def __init__(self, payload):
        self.payload = payload


class Ping(BaseGitHubEvent):

    def __call__(self):
        return


class PullRequest(BaseGitHubEvent):

    build_actions = (
        'opened',
        'reopened',
        'synchronize',
    )

    def __init__(self, payload):
        pr_dict = payload['pull_request']
        self.repo = payload['repository']['full_name']
        self.merge_commit = pr_dict['merge_commit_sha']
        self.branch = pr_dict['head']['ref']   # dont really care about branch
        self.number = pr_dict['number']        # pr number is more important
        self.branch = pr_dict['head']['sha1']  # but we need to pass status
                                               # somewhere
        self.pr_dict = pr_dict
        super(PullRequest, self).__init__(payload)

    def __call__(self):
        if not self.pr_dict['mergeable']:
            return
        if self.payload['action'] not in self.build_actions:
            return
        labels = github.sync_get(self.pr_dict['issue_url']).json()['labels']
        self.build(labels)

    def build(self, labels):
        print("Building against labels: {0}".format(labels))
        # get master sha1


class IssueComment(BaseGitHubEvent):

    def __call__(self):
        # body = self.payload['comment']['body']
        # commenter = self.payload['comment']['user']['login']
        # if commenter == config.github_user: pass
        # import ipdb;ipdb.set_trace()

        # admins
        # "@{0} {1}".format(config.github_user, 'merge')
        # build against all, get green then merge it

        # developers
        # "@{0} {1}".format(config.github_user, 'try')
        # build against labels
        pass


handler = {
    'pull_request': PullRequest,
    'ping': Ping,
    'issue_comment': IssueComment,
}
