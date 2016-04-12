import pprint
from .github import BUILDS  # One day, redis here
from .. import github


class BaseBuildbotEvent(object):

    def __init__(self, payload):
        props = {k: v for k, v, s in payload['build']['properties']}
        self.suite = props['suite']
        self.head_commit = props['head_commit']
        self.merge_commit = props['revision']
        self.builder = payload['build']['builderName']
        self.repo = props['repo']
        self.payload = payload
        self.props = props

    def get_all_statuses(self):
        return github.exhaust_pagination(
            github.sync_get(
                "repos/{0}/commits/{1}/statuses".format(
                    self.repo, self.head_commit
                )
            )
        )

    def post_status(self, context, status, link=None):
        payload = {'context': context, 'state': status}
        if link:
            payload.update({'target_url': link})
        print("Posting status: {0}".format(payload))
        return github.sync_post(
            "repos/{0}/statuses/{1}".format(self.repo, self.head_commit),
            json=payload
        )

    def __call__(self):
        raise NotImplementedError()



class BuildStarted(BaseBuildbotEvent):

    def __call__(self):
        print("Build of {0} started for {1} against {2}".format(self.builder, self.suite, self.merge_commit))
        pending_suite = False
        statuses = self.get_all_statuses()
        for status in statuses:
            if status['context'] == self.suite and status['state'] == 'pending':
                pending_suite = True
        if not pending_suite:
            self.post_status(self.suite, 'pending')
        for status in statuses:
            if status['context'] == self.builder:
                self.post_status(self.builder, 'pending')
                break


class BuildFinished(BaseBuildbotEvent):

    def __call__(self):
        print("Build of {0} finished for {1} against {2}".format(self.builder, self.suite, self.merge_commit))
        build_text = self.payload['build']['text']
        
        existing_status = None
        for status in self.get_all_statuses():
            if status['context'] == self.builder:
                existing_status = status
        if 'failed' in build_text:
            for step in self.payload['build']['steps']:
                link = None
                try:
                    if 'failed' in step['text']:
                        try:
                            link = step['logs'][0][1]
                        except:
                            pass  # might be no link
                        self.post_status(self.builder, 'failure', link)
                except KeyError:
                    self.post_status(self.builder, 'failure', link)
            if not self.payload['build']['steps']:
                self.post_status(self.builder, 'failure')

            BUILDS[self.merge_commit][self.suite][self.builder] = False
            print("Build of {0} failed for {1} against {2}".format(self.builder, self.suite, self.merge_commit))
        elif 'successful' in build_text:
            if existing_status:  # this builder was previously reported on
                self.post_status(self.builder, 'success')
            BUILDS[self.merge_commit][self.suite][self.builder] = True
            print("Build of {0} succeeded for {1} against {2}".format(self.builder, self.suite, self.merge_commit))
        else:
            BUILDS[self.merge_commit][self.suite][self.builder] = False
            self.post_status(self.builder, 'failure', '-'.join(build_text))
            print("Build of {0} errored for {1} against {2}".format(self.builder, self.suite, self.merge_commit))

        suite_results = BUILDS[self.merge_commit][self.suite].values()

        if all([True for result in suite_results if result in (True, False)]):
            # this suite is complete, so report on it and then drop the key
            if any([True for result in suite_results if result is False]):  # did anything fail?
                if self.suite != self.builder:  # avoid overwriting link
                                                # in case of leaf suite
                    self.post_status(self.suite, 'failure')
            else:
                self.post_status(self.suite, 'success')
            del BUILDS[self.merge_commit][self.suite]
            # if there are no more suites left to run for this commit, drop it
            if not BUILDS[self.merge_commit]:
                del BUILDS[self.merge_commit]
        pprint.pprint(BUILDS)



handler = {
    'buildStarted': BuildStarted,
    'buildFinished': BuildFinished,
}
