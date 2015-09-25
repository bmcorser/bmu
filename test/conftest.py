import pytest

import collections
import os

@pytest.fixture(scope='session')
def constants():
    here = os.path.dirname(__file__)
    GITHUB_API = 'https://api.github.com'
    constants_dict = {
        'GITHUB_API': GITHUB_API,
    }
    with open(os.path.join(here, '..', 'GITHUB_TOKEN'), 'r') as GHT:
        constants_dict['GITHUB_TOKEN'] = GHT.read().rstrip('\n')
    nt = collections.namedtuple('constants', constants_dict.keys())
    return nt(**constants_dict)