import requests


def test_event(system, github):
    create_resp = github('post', "repos/bmcorser/{0}/hooks".format(system.github_repo))
    create_resp = github(
        'post',
        "repos/bmcorser/{0}/hooks".format(system.github_repo),
        json={
            'name': 'web',
            'config': {'url': system.public_url, 'content_type': 'json'}
        }
    )
    assert create_resp.ok
