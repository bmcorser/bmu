from setuptools import setup

VERSION = '0.0.1'

setup(
    name='bmu',
    version=VERSION,
    description='GitHub/Buildbot integration service',
    author='@bmcorser',
    author_email='bmcorser@gmail.com',
    url='https://github.com/bmcorser/bmu',
    packages=['bmu'],
    install_requires=[
        'grequests',
        'klein',
        'plumbum',
        'pycrypto',
        'pyyaml',
        'requests',
    ],
    tests_require=['pytest'],
)
