# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Pidstore config."""

from __future__ import absolute_import, print_function

import pkg_resources

PIDSTORE_PROVIDERS = [
    'invenio_pidstore.providers.recordid:RecordID',
    'invenio_pidstore.providers.local_doi:LocalDOI',
]

EXTRA_PIDSTORE_PROVIDERS = [
    ('datacite', 'invenio_pidstore.providers.datacite:DataCite', ),
]

for dependency, provider in EXTRA_PIDSTORE_PROVIDERS:
    try:
        pkg_resources.get_distribution(dependency)
    except pkg_resources.DistributionNotFound:
        import warnings
        warnings.warn("Dependency {0} is required for provider {1}".format(
            dependency, provider.split(":")[-1]), ImportWarning)
    else:
        PIDSTORE_PROVIDERS.append(provider)

PIDSTORE_OBJECT_TYPES = ['rec', ]
"""
Definition of supported object types
"""

PIDSTORE_DATACITE_OUTPUTFORMAT = 'dcite'
"""
Output format used to generate the DataCite
"""

PIDSTORE_DATACITE_RECORD_DOI_FIELD = 'doi'
"""
Field name in record model (JSONAlchemy)
"""

PIDSTORE_DATACITE_SITE_URL = None
"""
Site URL to use when minting records.
"""
