from bmu import github
from bmu import label


def test_event(system, new_pr, bmu_conf, echoserver):
    label.init()
    repo_labels = sorted(label.get_existing_labels(system.github_repo['full_name']))
    proc = echoserver.start(2)
    label_resp = github.sync_request(
        'patch',
        "repos/bmcorser/{0}/issues/{1}".format(
            system.github_repo['name'],
            new_pr['number'],
        ),
        json={'labels': repo_labels[2:4]}
    )
    assert label_resp.ok
    data = echoserver.get_data(proc)
    assert [event['action'] for event in data] == ['labeled', 'labeled']
