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

    def post_status(self, context, status, link=None):
        payload = {'context': context, 'state': status}
        if link:
            payload.update({'target_url': link})
        return github.sync_post(
            "repos/{0}/statuses/{1}".format(self.repo, self.head_commit),
            json=payload
        )

    def __call__(self):
        props = {k: v for k, v, s in self.payload['build']['properties']}
        self.suite = props['suite']
        merge_commit = props['revision']
        self.head_commit = props['head_commit']
        self.builder = self.payload['build']['builderName']
        self.repo = props['repo']

        build_text = self.payload['build']['text']
        if 'failed' in build_text:
            for step in self.payload['build']['steps']:
                if 'failed' in step['text']:
                    link = None
                    try:
                        link = step['logs'][0][1]
                    except:
                        pass  # might be no link
                    self.post_status(self.builder, 'failure', link)

            BUILDS[merge_commit][self.suite][self.builder] = False
            print("Build of {0} failed for {1}".format(self.builder, merge_commit))
        elif 'success' in build_text:
            BUILDS[merge_commit][self.suite][self.builder] = True
            print("Build of {0} suceeded for {1}".format(self.builder, merge_commit))
        else:
            BUILDS[merge_commit][self.suite][self.builder] = False
            self.post_status(self.builder, 'failure', '-'.join(build_text))
            print("Build of {0} did something else for {1}".format(self.builder, merge_commit))
        print(build_text)

        def is_done(result):
            return result in (True, False)

        def is_false(result):
            return result is False

        suite_results = BUILDS[merge_commit][self.suite].values()

        if all(map(is_done, suite_results)):
            # this suite is complete, so report on it and then drop the key
            if any(map(is_false, suite_results)):
                self.post_status(self.suite, 'failure')
            else:
                self.post_status(self.suite, 'success')
            del BUILDS[merge_commit][self.suite]
            # if there are no more suites left to run for this commit, drop it
            if not BUILDS[merge_commit]:
                del BUILDS[merge_commit]



handler = {
    'buildStarted': BuildStarted,
    'buildFinished': BuildFinished,
}
