from . import config


def get_label_names(parental_namespace, label_tree):
    if isinstance(label_tree, basestring):
        return ["{0}/{1}".format(parental_namespace, label_tree)]
    keys = label_tree.keys()
    if len(keys) > 1:
        raise Exception('Use single-key dicts in config')
    namespace = keys[0]
    path = "{0}/{1}".format(parental_namespace, namespace)
    names = [path]
    sublabels = label_tree[namespace]
    for sublabel_tree in sublabels:
        names.extend(get_label_names(path, sublabel_tree))
    return names

def init():
    labels_list = []
    for user, repos in config.repos.items():
        for repo, labels in repos.items():
            for label_tree in labels:
                labels_list.extend(
                    get_label_names(config.namespace, label_tree)
                )
    import ipdb;ipdb.set_trace()
    resp = bmu.github.sync_post(
        "repos/bmcorser/{0}/labels".format(system.github_repo['name']),
        json={'name': 'fff', "color": "f29513"},
    )
