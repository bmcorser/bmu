'Constants module'
import os as __os


def __get_constant(name):
    '''
    Get a constant from a file in the repo root, or from an evironment variable
    with a matching name
    '''
    here = __os.path.dirname(__file__)
    try:
        with open(__os.path.join(here, '..', name), 'r') as __constant_fh:
            return __constant_fh.read().rstrip('\n')
    except IOError as exc:
        if exc.errno == 2:
            return __os.environ[name]
        else:
            raise

GITHUB_HEADER_SIGNATURE = 'X-Hub-Signature'
GITHUB_TOKEN = __get_constant('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = __get_constant('GITHUB_WEBHOOK_SECRET')
