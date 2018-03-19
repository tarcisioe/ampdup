from sys import version_info as py_version
from setuptools import setup, find_packages


VERSION = '0.0.8'

VERSION_REQUIREMENTS = []

if py_version < (3, 7):
    VERSION_REQUIREMENTS += [
        'asyncio-contextmanager',
        'dataclasses',
    ]

setup(
    name='ampdup',
    version=VERSION,
    url='https://gitlab.com/tarcisioe/ampdup',
    download_url=('https://gitlab.com/tarcisioe/ampdup/repository/'
                  'archive.tar.gz?ref=' + VERSION),
    keywords=['mpd', 'type', 'async'],
    maintainer='Tarcísio Eduardo Moreira Crocomo',
    maintainer_email='tarcisio.crocomo+pypi@gmail.com',
    description='A type-hinted async python mpd client library.',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    install_requires=VERSION_REQUIREMENTS + [
        'curio',
    ],
)
