import requests


def test_event(system, github):
    system.git_run(['checkout', '-b', 'ben/hello'])
    map(system.local_repo.commit, 'abcde')
    system.git_run(['push', 'origin', 'ben/hello'])
    resp = github(
        'post',
        'repos/bmcorser/{0}/pulls'.format(system.github_repo['name']),
        json={'title': 'tit', 'base': 'master', 'head': 'ben/hello'}
    )
    import ipdb;ipdb.set_trace()
