import pytest

import collections
from bmu.constants import __get_constant


@pytest.fixture(scope='session')
def constants():
    GITHUB_API = 'https://api.github.com'
    constants_dict = {
        'GITHUB_API': GITHUB_API,
    }
    constants_dict['GITHUB_TOKEN'] = __get_constant('GITHUB_TOKEN')
    constants_dict['GITHUB_WEBHOOK_SECRET'] = __get_constant('GITHUB_WEBHOOK_SECRET')
    nt = collections.namedtuple('constants', constants_dict.keys())
    return nt(**constants_dict)
