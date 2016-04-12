import functools
import os
import re
import time

import requests
import grequests

from . import constants
from . import config

RE_HYPERMEDIA = re.compile('<(?P<link>.*?)>; rel="(?P<rel>.*?)"')

def call_json(response):
    # import ipdb;ipdb.set_trace()
    return response.json()


def key(name):
    'Return a closure that returns the passed key from the passed data'
    def get(data):
        # import ipdb;ipdb.set_trace()
        return data[name]
    return get


def sync_request(method, url, use_gevent=False, **kwargs):
    'Close a requests request with configured authentication'
    if not url.startswith('https://'):
        url = os.path.join(constants.GITHUB_API, url)
    auth_tuple = (config.github_user, config.github_token)
    mod = grequests if use_gevent else requests
    def maybe_timeout():
        return getattr(mod, method)(url, auth=auth_tuple, timeout=2, **kwargs)
    try:
        return maybe_timeout()
    except requests.exceptions.ReadTimeout:
        # retry once
        return maybe_timeout()


def exhaust_pagination(resp):
    collection = resp.json()
    link = resp.headers.get('link')
    if link:
        next_url = {rel: url for url, rel in re.findall(RE_HYPERMEDIA, link)}.get('next')
        if next_url:
            time.sleep(0.5)  # don't anger GitHub
            collection.extend(exhaust_pagination(sync_request('get', next_url)))
    return collection


for __method in ['post', 'get', 'delete']:
    globals()["sync_{0}".format(__method)] = functools.partial(sync_request,
                                                               __method)
