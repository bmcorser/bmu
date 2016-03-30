import pytest

import os
import yaml
from bmu import config as bmu_config
from bmu import constants
from bmu.config import ConfigError

@pytest.yield_fixture(scope='function')
def tmp_config(tmp):
    os.environ[constants.CONF_PATH] = tmp
    yield tmp
    del os.environ[constants.CONF_PATH]


@pytest.fixture(scope='function')
def config_values():
    return {
        'repos': ['d', 'e', 'f'],
        'developers': ['g', 'h', 'i'],
        'mergers': ['j'],
    }


def test_raises_on_bad_name():
    with pytest.raises(ConfigError) as excinfo:
        bmu_config.__set_config('cakes')
    message = excinfo.value.message
    assert 'cakes' in message
    assert 'not a recognised' in message


def test_raises_on_empty_yaml(tmp_config):
    with pytest.raises(ConfigError) as excinfo:
        bmu_config.populate()
    assert 'YAML was empty' in excinfo.value.message


def test_raises_on_bad_yaml(tmp_config):
    with open(tmp_config, 'w') as fh:
        fh.write('bah\n  new: \n{:-\n\n$!')
        fh.flush()
    with pytest.raises(ConfigError) as excinfo:
        bmu_config.populate()
    assert 'parse' in excinfo.value.message


def test_raises_on_missing_config():
    with pytest.raises(ConfigError) as excinfo:
        bmu_config.populate()
    assert 'is required' in excinfo.value.message


def test_config_set_from_yaml(tmp_config, config_values):
    with open(tmp_config, 'w') as fh:
        fh.write(yaml.dump(config_values))
        fh.flush()
    bmu_config.populate()
    for name, expected_value in config_values.items():
        assert getattr(bmu_config, name) == expected_value


def test_config_set_from_env(tmp_config, config_values):
    os.environ['BMU_GITHUB_USER'] = 'x'
    with open(tmp_config, 'w') as fh:
        fh.write(yaml.dump(config_values))
        fh.flush()
    bmu_config.populate()
    assert bmu_config.github_user == 'x'


def test_config_env_overrides_yaml(tmp_config, config_values):
    os.environ['BMU_GITHUB_USER'] = 'y'
    with open(tmp_config, 'w') as fh:
        fh.write(yaml.dump(config_values))
        fh.flush()
    bmu_config.populate()
    for name, expected_value in config_values.items():
        if name != 'github_user':
            assert getattr(bmu_config, name) == expected_value
    assert bmu_config.github_user == 'y'

