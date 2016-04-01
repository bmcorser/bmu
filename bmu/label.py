import functools
import operator
import grequests
from . import config
from . import github


def get_label_names(namespace, label_tree):
    if isinstance(label_tree, basestring):
        return ["{0}/{1}".format(namespace, label_tree)]
    keys = label_tree.keys()
    if len(keys) > 1:
        raise Exception('Use single-key dicts in config')
    name = keys[0]
    prefix = "{0}/{1}".format(namespace, name)
    names = set([prefix])
    descendants = label_tree[name]
    for tree in descendants:
        names.update(get_label_names(prefix, tree))
    return names


def get_existing_labels(user_repo):
    resp = github.sync_get("repos/{0}/labels".format(user_repo))
    get_name = operator.itemgetter('name')
    is_bmu = lambda name: name.startswith(config.namespace)
    return set(filter(is_bmu, map(get_name, resp.json())))


def check_create_resps(resps):
    for resp in resps:
        if not resp.ok:
            for err in resp.json()['errors']:
                if err['code'] == 'already_exists':
                    return
            raise Exception('Could not create label')


def delete_create(user_repo, label_set):
    existing_labels = get_existing_labels(user_repo)
    create_fn = functools.partial(github.sync_post,
                                  "repos/{0}/labels".format(user_repo),
                                  use_gevent=True)
    create = [
        create_fn(json={'name': name, "color": "0074d9"})
        for name in label_set.difference(existing_labels)
    ]
    create_resps = grequests.map(create)
    check_create_resps(create_resps)
    delete = []
    for name in existing_labels.difference(label_set):
        delete.append(
            github.sync_delete(
                "repos/{0}/labels/{1}".format(user_repo, name),
                use_gevent=True,
            )
        )
    delete_resps = grequests.map(delete)
    assert all(map(lambda req: req.ok, delete_resps))


def get_configured_labels(user_repo):
    user, repo = user_repo.split('/')
    label_trees = config.repos[user][repo]
    label_set = set()
    for label_tree in label_trees:
        label_set.update(
            get_label_names(config.namespace, label_tree)
        )
    return label_set


def init():
    for user, repos in config.repos.items():
        for repo, labels in repos.items():
            user_repo = "{0}/{1}".format(user, repo)
            label_set = set([config.namespace])
            for label_tree in labels:
                label_set.update(
                    get_label_names(config.namespace, label_tree)
                )
            delete_create(user_repo, label_set)
