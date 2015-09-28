import pytest

from hashlib import sha1
import hmac

from bmu.validate import validate_content

SECRET = 'real-secret'


@pytest.fixture
def args():
    content = 'abc'
    sig = hmac.new(SECRET, 'abc', sha1).digest().encode('base64').rstrip('\n')
    return SECRET, sig, content


def test_validate_content_ok(args):
    validate_content(*args)


def test_validate_content_bad(args):
    secret, _, content = args
    with pytest.raises(Exception) as exc:
        validate_content(secret, 'no-secret', content)
        assert 'signature' in exc.message
