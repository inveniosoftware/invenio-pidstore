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

"""Record identifier model tests."""

from __future__ import absolute_import, print_function

from invenio_db import db

from invenio_pidstore.models import RecordIdentifier


def test_record_identifier(app):
    """Test base provider."""
    with app.app_context():
        assert RecordIdentifier.next() == 1
        assert RecordIdentifier.next() == 2
        assert RecordIdentifier.max() == 2

        # Mess up the sequence
        with db.session.begin_nested():
            obj = RecordIdentifier(recid=3)
            db.session.add(obj)

        assert RecordIdentifier.max() == 3

        # This tests a particular problem on PostgreSQL which is using
        # sequences to generate auto incrementing columns and doesn't deal
        # nicely with having values inserted in the table.
        assert RecordIdentifier.next() == 4

        RecordIdentifier.insert(10)
        assert RecordIdentifier.next() == 11
        assert RecordIdentifier.max() == 11

        RecordIdentifier.insert(7)
        assert RecordIdentifier.max() == 11
        assert RecordIdentifier.next() == 12
