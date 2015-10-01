# coding: utf-8

import pytest

import collections
import copy
import functools
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid

from Crypto.PublicKey import RSA
import requests

from bmu import github, config


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


def ngrok_public_url():
    url = 'http://localhost:4040/api/tunnels/command_line'
    while True:
        try:
            resp = requests.get(url)
            return resp.json()['public_url']
        except (requests.ConnectionError, KeyError):
            pass


@pytest.yield_fixture(scope='session')
def ngrok_server():
    ngrok_path = os.path.join(os.path.dirname(__file__), 'ngrok')
    process = run_silent([ngrok_path, 'http', '9000'])
    public_url = ngrok_public_url()
    yield public_url
    process.terminate()

@pytest.yield_fixture(scope='session')
def github_repo():
    name = "bmu-{0}".format(uuid.uuid4().hex[:7])
    print("Creating GitHub repo {0} ...".format(name))
    create_resp = github.sync_post('user/repos', json={'name': name})
    assert create_resp.ok
    yield create_resp.json()
    print("Deleting GitHub repo {0} ...".format(name))
    delete_resp = github.sync_delete("repos/bmcorser/{0}".format(name))
    assert delete_resp.ok

@pytest.yield_fixture(scope='session')
def bmu_conf(github_repo):
    conf_yaml = tempfile.NamedTemporaryFile(delete=False)
    user, _, repo = github_repo['full_name'].partition('/')
    conf_yaml.write('''\
repos:
  {0}:
    {1}:
      - a:
        - b
        - c
      - d:
        - e:
          - f
          - g
      - h
mergers:
 - {1}
'''.format(user, repo))
    conf_yaml.file.flush()
    conf_yaml.close()
    config.populate(conf_yaml.name)
    yield conf_yaml.name
    os.remove(conf_yaml.name)


@pytest.fixture
def bmu_server():
    def start_server(cli_args):
        process = run_silent(['python', '-m', 'bmu'] + cli_args)
        return process


@pytest.fixture
def echoserver(ngrok_server):

    def start_server(n, port=9000):
        print("Starting kamikaze echoserver for {0} requests ...".format(n))
        process = run_silent(
            ['python', 'echoserver.py', '-n', str(n), '-p', str(port)],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=os.path.abspath(os.path.dirname(__file__)),
        )
        awake = None
        fmt_str = "When asked if awake, the echo server at {0} said: {1}"
        while not awake:
            print("Pinging kamikaze echoserver ...")
            url = "{0}/awake".format(ngrok_server)
            resp = requests.get(url)
            if resp.ok:
                print(fmt_str.format(ngrok_server, resp.content))
                awake = True
        return process

    def get_data(proc, wait=True, force=False):
        retcode = proc.poll()
        if retcode is None and not force and not wait:
            raise Exception('The echo server is not ripe for harvesting')
        elif retcode is None and force:
            ripe = None
            while not ripe:
                print('Exhausting echoserver by force ...')
                resp = requests.post(ngrok_server)
                if resp.status_code == 502:
                    ripe = True
        elif retcode is None and wait and not force:
            ripe = None
            while not ripe:
                print("Waiting for kamikaze echoserver to be exhausted ...")
                resp = requests.get("{0}/awake".format(ngrok_server))
                if resp.status_code == 502:
                    ripe = True
        if proc.poll() is None:
            raise Exception('Something went wrong')
        out, _ = proc.communicate()
        file_list = json.loads(out)
        data = map(lambda x: json.load(open(x)), file_list)
        map(os.remove, file_list)
        return data

    echoserver_dict = {
        'start': start_server,
        'get_data': get_data,
    }
    return collections.namedtuple('echoserver', echoserver_dict.keys())(**echoserver_dict)


@pytest.yield_fixture(scope='session')
def ssh_wrapper(github_repo):
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

    with open(public.name, 'r') as pubkey_file:
        pubkey_content = pubkey_file.read()
    print('Adding temp pubkey to GitHub ...')
    create_resp = github.sync_post(
        'user/keys',
        json={'title': github_repo['name'], 'key': pubkey_content}
    )
    assert create_resp.ok
    key_id = create_resp.json()['id']

    yield wrapper.name

    map(os.remove, (wrapper.name, private.name, public.name))
    print('Deleting temp pubkey from GitHub ...')
    delete_resp = github.sync_delete("user/keys/{0}".format(key_id))
    assert delete_resp.ok


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
    global git_time
    git_time = 1329000000

    def incr_time():
        'Increment the time that Git knows about'
        global git_time
        git_time += 100
        os.environ.update({
            'GIT_COMMITTER_DATE': "{0} +0000".format(git_time),
            'GIT_AUTHOR_DATE': "{0} +0000".format(git_time),
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
        return out.split()[1].strip(']'), copy.copy(git_time)

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
        'time': git_time,
    }
    return collections.namedtuple('repo', repo_dict.keys())(**repo_dict)


@pytest.fixture
def github_webhook(ngrok_server, bmu_conf, github_repo):
    print("Creating GitHub webhook for {0} ...".format(github_repo['name']))
    create_resp = github.sync_post(
        "repos/bmcorser/{0}/hooks".format(github_repo['name']),
        json={
            'name': 'web',
            'events': [
                'pull_request',
                'issue_comment',
            ],
            'config': {
                'url': os.path.join(ngrok_server, 'github'),
                'content_type': 'json',
                'secret': config.github_webhook_secret,
            }
        }
    )
    assert create_resp.ok
    return create_resp.json()

@pytest.yield_fixture
def system(ngrok_server, bmu_server, github_repo, github_webhook, ssh_wrapper):
    local_repo = create_temp_repo()
    git_run(local_repo.root, [
        'remote',
        'add',
        'origin',
        "git@github.com:bmcorser/{0}".format(github_repo['name']),
    ])
    map(local_repo.commit, 'abcde')
    print("Pushing local repo to GitHub ...")
    retcode, (out, err) = git_run(
        local_repo.root,
        ['push', 'origin', 'master'],
        env={'GIT_SSH': ssh_wrapper}
    )
    system_dict = {
        'public_url': ngrok_server,
        'start_bmu': bmu_server,
        'github_repo': github_repo,
        'github_webhook': github_webhook,
        'local_repo': local_repo,
        'git_run': functools.partial(
            git_run,
            local_repo.root,
            env={'GIT_SSH': ssh_wrapper}
        ),
    }
    nt = collections.namedtuple('system', system_dict.keys())
    yield nt(**system_dict)
    local_repo.cleanup()


@pytest.yield_fixture
def new_pr(system, echoserver):
    name = "branch-{0}".format(uuid.uuid4().hex[:7])
    system.git_run(['fetch', 'origin'])
    system.git_run(['reset', '--hard', 'origin/master'])
    system.git_run(['checkout', '-b', name])
    map(system.local_repo.commit, 'abcde')
    system.git_run(['push', 'origin', name])
    print("Creating PR for {0} on GitHub  ...".format(name))
    proc = echoserver.start(1)
    create_resp = github.sync_post(
        'repos/bmcorser/{0}/pulls'.format(system.github_repo['name']),
        json={
            'title': "PR for {0}".format(name),
            'base': 'master',
            'head': name,
        }
    )
    pr_json = create_resp.json()
    assert echoserver.get_data(proc)[0]['payload']['action'] == 'opened'
    yield pr_json
    print("Closing PR for {0} on GitHub  ...".format(name))
    close_resp = github.sync_request(
        'patch',
        'repos/{0}/{1}/pulls/{2}'.format(
            config.github_user,
            system.github_repo['name'],
            pr_json['number'],
        ),
        json={'state': 'closed'},
    )
    assert close_resp.ok
