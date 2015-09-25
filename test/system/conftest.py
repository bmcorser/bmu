# coding: utf-8

import pytest

import collections
import copy
from Crypto.PublicKey import RSA
import json
import os
import shutil
import subprocess
import tempfile
import uuid

import requests


def run_silent(cmd, can_fail=False, **overrides):
    'Run a command, but discard its output. Raise on error'
    with open(os.devnull, 'w') as DEVNULL:
        kwargs = {
            'stdout': DEVNULL,
            'stderr': DEVNULL,
        }
        kwargs.update(overrides)
        try:
            return subprocess.Popen(cmd, **kwargs)
        except subprocess.CalledProcessError as exc:
            if can_fail:
                pass
            else:
                raise


def git_run(directory, git_subcommand, return_proc=False, **popen_kwargs):
    '''
    Start a process to run the passed git subcommand in the passed directory
    Returns the return code and formatted output in a tuple nest like this:

        (returncode, (out, err))

    '''
    default_kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'cwd': directory,
    }
    default_kwargs.update(popen_kwargs)
    proc = subprocess.Popen(['git'] + git_subcommand,
                            **default_kwargs)
    if return_proc:
        return proc
    retcode = proc.wait()
    return retcode, proc.communicate()


@pytest.yield_fixture(scope='session')
def ngrok_server():
    ngrok_path = os.path.join(os.path.dirname(__file__), 'ngrok')
    process = run_silent([ngrok_path, 'http', '9000'])
    url = 'http://localhost:4040/api/tunnels/command_line'
    tunnel_data = json.loads(requests.get(url).content)
    yield tunnel_data['public_url']
    process.terminate()


@pytest.fixture
def bmu_server():
    def start_server(opts):
        global process
        process = run_silent(['python', '-m', 'bmu'])
        return process


@pytest.fixture(scope='session')
def github(constants):
    def github_fn(method, path, **kwargs):
        fn = getattr(requests, method)
        url = os.path.join(constants.GITHUB_API, path)
        return fn(url, auth=('bmcorser', constants.GITHUB_TOKEN), **kwargs)
    return github_fn


@pytest.yield_fixture(scope='function')
def github_repo(constants, github):
    name = "bmu-{0}".format(uuid.uuid4().hex[:7])
    create_resp = github(
        'post',
        'user/repos',
        json={'name': name}
    )
    assert create_resp.ok
    yield name
    delete_resp = github(
        'delete',
        "repos/bmcorser/{0}".format(name)
    )
    assert delete_resp.ok


@pytest.fixture(scope='session')
def ssh_wrapper(github):
    WRAPPER_TEMPLATE = '''#!/bin/bash
ssh -i {0} $1 $2'''
    key = RSA.generate(2048)

    private = tempfile.NamedTemporaryFile(delete=False)
    os.chmod(private.name, 0600)
    private.write(key.exportKey('PEM'))
    private.file.flush()
    private.close()

    public = tempfile.NamedTemporaryFile(delete=False)
    public.write(key.publickey().exportKey('OpenSSH'))
    public.file.flush()
    public.close()

    wrapper = tempfile.NamedTemporaryFile(delete=False)
    wrapper.write(WRAPPER_TEMPLATE.format(private.name))
    wrapper.file.flush()
    wrapper.close()
    os.chmod(wrapper.name, 0755)

    return wrapper.name, (private.name, public.name)


def create_temp_repo():
    root_dir = tempfile.mkdtemp()
    # set up local
    local = os.path.join(root_dir, 'repo')
    os.mkdir(local)
    git_run(local, ['init'])
    user_name = 'bmu-test'
    user_email = 'bmu@test.com'
    git_run(local, ['config', 'user.name', user_name])
    git_run(local, ['config', 'user.email', user_email])

    # set up time-related things
    global time
    time = 1329000000

    def incr_time():
        'Increment the time that Git knows about'
        global time
        time += 100
        os.environ.update({
            'GIT_COMMITTER_DATE': "{0} +0000".format(time),
            'GIT_AUTHOR_DATE': "{0} +0000".format(time),
        })

    def touch(path):
        'Make a change to a file that Git will see'
        with open(os.path.join(local, path), 'w') as repo_file:
            repo_file.write(repr(uuid.uuid4().hex))

    def commit(name):
        path = os.path.join(local, name, 'README.md')
        try:
            os.mkdir(os.path.join(local, name))
        except OSError as exc:
            if exc.errno != 17:
                raise
        touch(path)
        git_run(local, ['add', name])
        retcode, (out, err) = git_run(
            local,
            ['commit', '-m', name],
            env=incr_time())
        return out.split()[1].strip(']'), copy.copy(time)

    touch('README.md')
    git_run(local, ['add', '.'])
    git_run(local, ['commit', '-m', 'Initial commit'])

    def cleanup():
        shutil.rmtree(root_dir)

    repo_dict = {
        'user_name': user_name,
        'user_email': user_email,
        'commit': commit,
        'touch': touch,
        'root': local,
        'cleanup': cleanup,
        'incr_time': incr_time,
        'time': time,
    }
    return collections.namedtuple('repo', repo_dict.keys())(**repo_dict)


@pytest.yield_fixture
def system(ngrok_server, bmu_server, github, github_repo, ssh_wrapper):
    local_repo = create_temp_repo()
    ssh_wrapper, (prikey, pubkey) = ssh_wrapper
    with open(pubkey, 'r') as pubkey_file:
        pubkey_content = pubkey_file.read()
    create_resp = github(
        'post',
        'user/keys',
        json={'title': github_repo, 'key': pubkey_content}
    )
    assert create_resp.ok
    key_id = create_resp.json()['id']
    git_run(local_repo.root, [
        'remote',
        'add',
        'origin',
        "git@github.com:bmcorser/{0}".format(github_repo),
    ])
    # git_run(local_repo.root, ['checkout', '-b', 'new-branch'])
    map(local_repo.commit, 'abcde')
    retcode, (out, err) = git_run(local_repo.root, ['push', 'origin', 'master'], env={'GIT_SSH': ssh_wrapper})
    system_dict = {
        'public_url': ngrok_server,
        'start_bmu': bmu_server,
        'remote_name': github_repo,
        'local_repo': local_repo,
    }
    nt = collections.namedtuple('system', system_dict.keys())
    yield nt(**system_dict)
    local_repo.cleanup()
    map(os.remove, (ssh_wrapper, prikey, pubkey))
    delete_resp = github('delete', "user/keys/{0}".format(key_id))
    assert delete_resp.ok
