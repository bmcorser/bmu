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


def delete_create(user_repo, label_set):
    existing_labels = get_existing_labels(user_repo)
    create_fn = functools.partial(github.sync_post,
                                  "repos/{0}/labels".format(user_repo),
                                  use_gevent=True)
    create = [
        create_fn(json={'name': name, "color": "0074d9"})
        for name in label_set.difference(existing_labels)
    ]
    assert all(map(lambda req: req.ok, grequests.map(create)))
    delete = []
    for name in existing_labels.difference(label_set):
        delete.append(
            github.sync_delete(
                "repos/{0}/labels/{1}".format(user_repo, name),
                use_gevent=True,
            )
        )
    assert all(map(lambda req: req.ok, grequests.map(delete)))


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
    # import ipdb;ipdb.set_trace()
