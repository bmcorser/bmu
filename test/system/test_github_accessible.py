import uuid
import bmu


def test_event(system):
    def make_pr(name):
        system.git_run(['fetch', 'origin'])
        system.git_run(['reset', '--hard', 'origin/master'])
        system.git_run(['checkout', '-b', name])
        map(system.local_repo.commit, 'abcde')
        system.git_run(['push', 'origin', name])
        resp = bmu.github.sync_post(
            'repos/bmcorser/{0}/pulls'.format(system.github_repo['name']),
            json={'title': 'tit', 'base': 'master', 'head': name}
        )
        return resp
    resp = make_pr(uuid.uuid4().hex)
    import ipdb;ipdb.set_trace()
