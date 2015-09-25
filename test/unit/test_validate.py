import pytest

from hashlib import sha1
import hmac

from bmu.validate import validate_content

@pytest.fixture
def args(constants):
    content = 'abc'
    secret = 'abc'
    sig = hmac.new(constants.WEBHOOK_SECRET, 'abc', sha1).digest().encode('base64').rstrip('\n')
    return constants.WEBHOOK_SECRET, sig, content

def test_validate_content_ok(args):
    validate_content(*args)

def test_validate_content_bad(args):
    secret, _, content = args
    with pytest.raises(Exception) as exc:
        validate_content(secret, 'abc', content)
        assert 'signature' in exc.message
