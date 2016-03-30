import setuptools

VERSION = '0.0.3'

setuptools.setup(
    name='bmu',
    version=VERSION,
    description='GitHub/Buildbot integration service',
    author='@bmcorser',
    author_email='bmcorser@gmail.com',
    url='https://github.com/bmcorser/bmu',
    packages=setuptools.find_packages(),
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
