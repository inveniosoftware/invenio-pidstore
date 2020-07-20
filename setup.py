# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that stores and registers persistent identifiers."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'Flask-Menu>=0.5.1',
    'invenio-admin>=1.2.0',
    'invenio-access>=1.0.0',
    'invenio-accounts>=1.0.0',
    'mock>=3.0.0',
    'pytest-invenio<=1.3.2',
    'SQLAlchemy-Continuum>=1.2.1',
]

extras_require = {
    'admin': [
        'invenio-admin>=1.2.0',
    ],
    'datacite': [
        'datacite>=0.1.0'
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0',
    ],
    'sqlite': [
        'invenio-db>=1.0.0',
    ],
    'docs': [
        'Sphinx>=1.8.5',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite') \
       or name.startswith(':'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.7.1',
]

install_requires = [
    'base32-lib>=1.0.1',
    'enum34>=1.1.6;python_version<"3.4"',
    'invenio-base>=1.2.2',
    'invenio-i18n>=1.2.0',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_pidstore', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-pidstore',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio identifier DOI',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-pidstore',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_db.alembic': [
            'invenio_pidstore = invenio_pidstore:alembic',
        ],
        'invenio_db.models': [
            'invenio_pidstore = invenio_pidstore.models',
        ],
        'invenio_base.apps': [
            'invenio_pidstore = invenio_pidstore:InvenioPIDStore',
        ],
        'invenio_base.api_apps': [
            'invenio_pidstore = invenio_pidstore:InvenioPIDStore',
        ],
        'invenio_pidstore.minters': [
            'recid = invenio_pidstore.minters:recid_minter',
            'recid_v2 = invenio_pidstore.minters:recid_minter_v2',
        ],
        'invenio_pidstore.fetchers': [
            'recid = invenio_pidstore.fetchers:recid_fetcher',
            'recid_v2 = invenio_pidstore.fetchers:recid_fetcher_v2',
        ],
        'invenio_admin.views': [
            'invenio_pidstore_pid = invenio_pidstore.admin:pid_adminview',
        ]
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
