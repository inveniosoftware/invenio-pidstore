# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Record identifier model tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import RecordIdentifier


def test_record_identifier(app, db):
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
