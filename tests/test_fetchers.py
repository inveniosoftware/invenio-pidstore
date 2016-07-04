# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Fetcher tests."""

from __future__ import absolute_import, print_function

import uuid

from invenio_pidstore import current_pidstore
from invenio_pidstore.fetchers import recid_fetcher
from invenio_pidstore.minters import recid_minter


def test_recid_fetcher(app):
    """Test base provider."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        data = {}
        minted_pid = recid_minter(rec_uuid, data)
        fetched_pid = recid_fetcher(rec_uuid, data)
        assert minted_pid.pid_value == fetched_pid.pid_value
        assert fetched_pid.pid_type == fetched_pid.provider.pid_type
        assert fetched_pid.pid_type == 'recid'


def test_register_fetcher(app):
    """Test base provider."""
    with app.app_context():
        current_pidstore.register_fetcher('anothername', recid_minter)
