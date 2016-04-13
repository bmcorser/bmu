import collections
import json

from redlock import RedLock
from redis import StrictRedis

from constants import REDIS_BUILDS as key


def _rehydrate_state(state_):
    defaultdict = lambda: collections.defaultdict(defaultdict)
    settable = defaultdict()
    settable.update(state_)
    return settable

def _get_lock(sha):
    key = "bmu:lock:{0}".format(sha)
    return RedLock(key, [{'url': 'redis://localhost/3'}], retry_times=5, retry_delay=1000)

redis = StrictRedis(db=3)


def _debug():
    'Print the whole API for debugging purposes'
    import pprint
    state_ = {}
    for key in redis.keys('*'):
        state_[key] = json.loads(redis.get(key))
    pprint.pprint(state_)
    

def get(merge_commit, suite=None, builder=None):
    'Get some state node'
    root = _rehydrate_state(json.loads(redis.get(merge_commit) or '{}'))
    if not suite:
        return root
    if not builder:
        return root.get(suite, None)
    return root.get(suite, {}).get(builder, None)


def _set(merge_commit, state_):
    return redis.set(merge_commit, json.dumps(state_))


def set_frag(merge_commit, state_frag, suite=None, builder=None):
    'Set some state node'
    with _get_lock(merge_commit):
        state_ = get(merge_commit)
        if not suite:
            state_.update(state_frag)
            return _set(merge_commit, state_)
        if not builder:
            state_[suite] = state_frag
            return _set(merge_commit, state_)
        state_[suite][builder] = state_frag
        return _set(merge_commit, state_)



def set(merge_commit, suite, builder, value):
    'Set some state leaf'
    return set_frag(merge_commit, value, suite, builder)


def drop(merge_commit, suite=None, builder=None):
    'Drop some state node'
    if not suite:
        redis.delete(merge_commit)
        return
    state_ = get(merge_commit)
    if not builder:
        del state_[suite]
        return set_frag(merge_commit, state_)
    del state_[suite][builder]
    return set_frag(merge_commit, state_)
