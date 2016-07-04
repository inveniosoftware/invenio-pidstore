# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Resolver tests."""

from __future__ import absolute_import, print_function

import uuid

import pytest
from invenio_db import db
from invenio_records.api import Record

from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError, PIDRedirectedError, PIDUnregistered
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver


def test_resolver(app):
    """Test the class methods of PersistentIdentifier class."""
    status = [
        PIDStatus.NEW,
        PIDStatus.RESERVED,
        PIDStatus.REGISTERED,
        PIDStatus.DELETED,
    ]

    with app.app_context():
        i = 1
        rec_a = uuid.uuid4()

        # Create pids for each status with and without object
        for s in status:
            PersistentIdentifier.create('recid', i, status=s)
            i += 1
            if s != PIDStatus.DELETED:
                PersistentIdentifier.create(
                    'recid', i, status=s, object_type='rec', object_uuid=rec_a)
                i += 1

        # Create a DOI
        pid_doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=rec_a)

        # Create redirects
        pid = PersistentIdentifier.create(
            'recid', i, status=PIDStatus.REGISTERED)
        i += 1
        pid.redirect(PersistentIdentifier.get('recid', '2'))
        pid = PersistentIdentifier.create(
            'recid', i, status=PIDStatus.REGISTERED)
        pid.redirect(pid_doi)
        db.session.commit()

        # Start tests
        resolver = Resolver(
            pid_type='recid',
            object_type='rec',
            getter=lambda x: x)

        # Resolve non-existing pid
        pytest.raises(PIDDoesNotExistError, resolver.resolve, '100')
        pytest.raises(PIDDoesNotExistError, resolver.resolve, '10.1234/foo')

        # Resolve status new
        pytest.raises(PIDUnregistered, resolver.resolve, '1')
        pytest.raises(PIDUnregistered, resolver.resolve, '2')

        # Resolve status reserved
        pytest.raises(PIDUnregistered, resolver.resolve, '3')
        pytest.raises(PIDUnregistered, resolver.resolve, '4')

        # Resolve status registered
        pytest.raises(PIDMissingObjectError, resolver.resolve, '5')
        pid, obj = resolver.resolve('6')
        assert pid and obj == rec_a

        # Resolve status deleted
        pytest.raises(PIDDeletedError, resolver.resolve, '7')

        # Resolve status redirected
        try:
            resolver.resolve('8')
            assert False
        except PIDRedirectedError as e:
            assert e.destination_pid.pid_type == 'recid'
            assert e.destination_pid.pid_value == '2'

        try:
            resolver.resolve('9')
            assert False
        except PIDRedirectedError as e:
            assert e.destination_pid.pid_type == 'doi'
            assert e.destination_pid.pid_value == '10.1234/foo'

        doiresolver = Resolver(
            pid_type='doi',
            object_type='rec',
            getter=lambda x: x)
        pytest.raises(PIDDoesNotExistError, doiresolver.resolve, '1')
        pid, obj = doiresolver.resolve('10.1234/foo')
        assert pid and obj == rec_a


def test_resolver_deleted_object(app):
    """Test the class methods of PersistentIdentifier class."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        with db.session.begin_nested():
            record = Record.create({'title': 'test'})

            pid = PersistentIdentifier.create(
                'recid', '1', status=PIDStatus.REGISTERED,
                object_type='rec', object_uuid=rec_uuid)

        with db.session.begin_nested():
            pid.delete()
            record.delete()

        resolver = Resolver(
            pid_type='recid', object_type='rec', getter=Record.get_record)

        assert pytest.raises(PIDDeletedError, resolver.resolve, '1')
