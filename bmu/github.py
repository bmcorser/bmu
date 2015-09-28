import functools
import requests
import grequests
import treq
import os
from . import constants
from . import config


def call_json(response):
    # import ipdb;ipdb.set_trace()
    return response.json()


def key(name):
    'Return a closure that returns the passed key from the passed data'
    def get(data):
        # import ipdb;ipdb.set_trace()
        return data[name]
    return get


def request(method, url, **kwargs):
    'Close a treq request with configured authentication'
    if not url.startswith('https://'):
        url = os.path.join(constants.GITHUB_API, url)
    auth_tuple = (config.github_user, config.github_token)
    fn = getattr(treq, method)
    return fn(url.encode('utf-8'), auth=auth_tuple, **kwargs).addCallback(call_json)


def sync_request(method, url, use_gevent=False, **kwargs):
    'Close a requests request with configured authentication'
    if not url.startswith('https://'):
        url = os.path.join(constants.GITHUB_API, url)
    auth_tuple = (config.github_user, config.github_token)
    mod = grequests if use_gevent else requests
    return getattr(mod, method)(url, auth=auth_tuple, **kwargs)


for __method in ['post', 'get', 'delete']:
    globals()[__method] = functools.partial(request, __method)
    globals()["sync_{0}".format(__method)] = functools.partial(sync_request,
                                                               __method)
