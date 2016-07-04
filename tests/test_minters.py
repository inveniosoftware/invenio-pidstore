# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""Minter tests."""

from __future__ import absolute_import, print_function

import uuid

from invenio_pidstore import current_pidstore
from invenio_pidstore.minters import recid_minter


def test_recid_minter(app):
    """Test base provider."""
    with app.app_context():

        rec_uuid = uuid.uuid4()
        data = {}
        pid = recid_minter(rec_uuid, data)
        assert pid
        assert data['control_number'] == pid.pid_value
        assert pid.object_type == 'rec'
        assert pid.object_uuid == rec_uuid


def test_register_minter(app):
    """Test base provider."""
    with app.app_context():
        current_pidstore.register_minter('anothername', recid_minter)
