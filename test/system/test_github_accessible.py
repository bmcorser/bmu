from bmu import github
from bmu import label


def test_labels_are_created_by_bmu(system, new_pr, bmu_conf, echoserver):
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
    assert [event['payload']['action'] for event in data] == [
        'labeled',
        'labeled',
    ]
    print(bmu_conf)
    # import ipdb;ipdb.set_trace()
    comment_resp = github.sync_post(
        "repos/bmcorser/{0}/issues/{1}/comments".format(
            system.github_repo['name'],
            new_pr['number'],
        ),
        json={'body': '@bmcorser fff'}
    )
    assert comment_resp.ok
