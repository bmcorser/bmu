import uuid
from bmu import github
from bmu import label
import json


def test_event(system, bmu_conf, echoserver):
    def make_pr(name):
        system.git_run(['fetch', 'origin'])
        system.git_run(['reset', '--hard', 'origin/master'])
        system.git_run(['checkout', '-b', name])
        map(system.local_repo.commit, 'abcde')
        system.git_run(['push', 'origin', name])
        resp = github.sync_post(
            'repos/bmcorser/{0}/pulls'.format(system.github_repo['name']),
            json={'title': "PR for {0}".format(name), 'base': 'master', 'head': name}
        )
        return resp
    pr_json = make_pr("branch-{0}".format(uuid.uuid4().hex[:7])).json()
    repo_labels = sorted(label.get_existing_labels(system.github_repo['full_name']))
    proc = echoserver.start(1)
    resp = github.sync_request(
        'patch',
        "repos/bmcorser/{0}/issues/{1}".format(system.github_repo['name'], pr_json['number']),
        json={'labels': repo_labels[2:4]}
    )
    import ipdb;ipdb.set_trace()
