import requests


def test_event(system, github):
    def make_pr(name):
        system.git_run(['fetch', 'origin'])
        system.git_run(['reset', '--hard', 'origin/master'])
        system.git_run(['checkout', '-b', name])
        map(system.local_repo.commit, 'abcde')
        system.git_run(['push', 'origin', name])
        resp = github(
            'post',
            'repos/bmcorser/{0}/pulls'.format(system.github_repo['name']),
            json={'title': 'tit', 'base': 'master', 'head': name}
        )
        return resp
    # import ipdb;ipdb.set_trace()
