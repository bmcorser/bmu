from .github import BUILDS  # One day, redis here
from .. import github


class BaseBuildbotEvent(object):
    def __init__(self, payload):
        self.payload = payload

    def __call__(self):
        raise NotImplementedError()


class BuildStarted(BaseBuildbotEvent):

    def __call__(self):
        props = {k: v for k, v, s in self.payload['build']['properties']}
        resp = github.sync_post(
            "repos/{0}/statuses/{1}".format(props['repo'], props['head_commit']),
            json={
                'state': 'pending',
                'context': props['suite'],
            }
        )
        print(resp)
        print("Build started for {0}".format(props['revision']))


class BuildFinished(BaseBuildbotEvent):

    def post_status(self, context, status):
        return github.sync_post(
            "repos/{0}/statuses/{1}".format(self.repo, self.head_commit),
            json={
                'context': context,
                'state': status,
            }
        )

    def __call__(self):
        # Bit more needed here
        # Need to do something around Redis to keep a track of what builds
        # belong to a particular label, then only say finished 'to' that
        # label 
        props = {k: v for k, v, s in self.payload['build']['properties']}
        self.suite = props['suite']
        merge_commit = props['revision']
        self.head_commit = props['head_commit']
        self.builder = self.payload['build']['builderName']
        self.repo = props['repo']

        if self.payload['build']['text'] == ['failed']:
            BUILDS[merge_commit][self.suite][self.builder] = False
            self.post_status(props['suite'], 'failure')
            print("Build failed for {0}".format(props['revision']))
        else:
            BUILDS[merge_commit][self.suite][self.builder] = True
            print("Build might have suceeded for {0}".format(props['revision']))

        def is_done(result):
            return result in (True, False)

        def is_false(result):
            return result is False

        suite_results = BUILDS[merge_commit][self.suite].values()

        if all(map(is_done, suite_results)):
            if any(map(is_false, suite_results)):
                self.post_status(self.suite, 'failure')
            else:
                self.post_status(self.suite, 'success')


handler = {
    'buildStarted': BuildStarted,
    'buildFinished': BuildFinished,
}
