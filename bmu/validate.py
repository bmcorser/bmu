'Validate that requests come from GitHub'
import hashlib
import hmac
import json

from . import constants
from . import config


def validate_content(secret, request_hash, content):
    'Validate some content is signed with the secret'
    our_hash = hmac.HMAC(secret, content, hashlib.sha1).hexdigest()
    if our_hash != request_hash:
        raise Exception('The request signature header was not correct')


def payload(request):
    'Validate a request really came from GitHub, try to return the payload'
    signature = request.getHeader(constants.GITHUB_API_HEADER_SIGNATURE)
    if not signature:
        raise Exception(
            "The request did not have the signature header: {0}".format(
                constants.GITHUB_API_HEADER_SIGNATURE
            )
        )
    head, _, request_hash = signature.partition('=')
    if head != 'sha1':
        raise Exception('The signature did not use the SHA1 hash function')
    content = request.content.read()
    validate_content(config.github_webhook_secret, request_hash, content)
    try:
        return json.loads(content)
    except:
        raise Exception('Could not parse JSON from request')
