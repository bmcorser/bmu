import os
import tempfile
import pytest


@pytest.yield_fixture(scope='function')
def tmp():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    yield tmp.name
    os.remove(tmp.name)
