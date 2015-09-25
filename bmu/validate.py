'Validate that requests come from GitHub'
from hashlib import sha1
import hmac

from bmu.constants import GITHUB_HEADER_SIGNATURE


def validate_content(secret, signature, content):
    'Validate some content is signed with the secret'
    content_hash = (
        hmac.new(secret, content, sha1)
            .digest()
            .encode("base64")
            .rstrip('\n')
    )
    if content_hash != signature:
        raise Exception('The request signature header was not correct')


def validate_request(request, secret):
    'Validate a request really came from GitHub'
    signature = request.getHeader(GITHUB_HEADER_SIGNATURE)
    if not signature:
        raise Exception(
            "The request did not have the signature header: {0}".format(
                GITHUB_HEADER_SIGNATURE
            )
        )
    content = request.content.read()
    validate_content(secret, signature, content)
