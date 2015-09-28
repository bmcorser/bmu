'Trigger builds'
from . import config


def send(pr):
    'Arrange a PullRequest object into buildbot change format and send it'
    config.buildbot_url
def trigger(changes, properties):
    'Send changes and properties to Buildbot'
    number = pr_dict['number']
    change = {
        'revision': pr_dict['head']['sha'],
        'when_timestamp': dateparse(pr_dict['created_at']),
        'branch': refname,
        'revlink': pr_dict['_links']['html']['href'],
        'repository': bmu_payload['repository']['clone_url'],
        'category': 'pull',
        # TODO: Get author name based on login id using txgithub module
        'author': bmu_payload['sender']['login'],
        'comments': 'GitHub Pull Request #%d (%d commit%s)' % (
            number, commits, 's' if commits != 1 else ''),
    }
    if options is None:
        options = {}

    handler = klass(options.get('secret', None),
                    options.get('strict', False),
                    options.get('codebase', None))
    return handler.process(request)
    pass

