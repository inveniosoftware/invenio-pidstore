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


"""Model tests."""

from __future__ import absolute_import, print_function

import uuid

import pytest
from invenio_db import db
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from invenio_pidstore.errors import PIDAlreadyExists, PIDDoesNotExistError, \
    PIDInvalidAction, PIDObjectAlreadyAssigned
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect


@patch('invenio_pidstore.models.logger')
def test_pid_creation(logger, app):
    """Test pid creation."""
    with app.app_context():
        assert PersistentIdentifier.query.count() == 0
        pid = PersistentIdentifier.create('doi', '10.1234/foo')
        assert PersistentIdentifier.query.count() == 1
        assert pid.pid_type == 'doi'
        assert pid.pid_value == '10.1234/foo'
        assert pid.pid_provider is None
        assert pid.status == PIDStatus.NEW
        assert pid.object_type is None
        assert pid.object_uuid is None
        assert logger.info.called

        rec_uuid = uuid.uuid4()
        pid = PersistentIdentifier.create(
            'rec', '2', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=rec_uuid)
        assert PersistentIdentifier.query.count() == 2
        assert pid.pid_type == 'rec'
        assert pid.pid_value == '2'
        assert pid.pid_provider is None
        assert pid.status == PIDStatus.REGISTERED
        assert pid.object_type == 'rec'
        assert pid.object_uuid == rec_uuid

        # Can't duplicate existing persistent identifier
        assert not logger.exception.called
        pytest.raises(
            PIDAlreadyExists, PersistentIdentifier.create, 'rec', '2')
        assert logger.exception.called

        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, PersistentIdentifier.create,
                          'rec', '2')
            assert logger.exception.call_args[0][0].startswith(
                "Failed to create")


def test_upgrades():
    """Test import of upgrades."""
    from invenio_pidstore import upgrades  # pragma: noqa


def test_pidstatus_as():
    """Test PID status."""
    assert PIDStatus.NEW.title == 'New'
    assert PIDStatus.RESERVED.title == 'Reserved'
    assert next(iter(PIDStatus)) == 'N'


def test_pid_get(app):
    """Test pid retrieval."""
    with app.app_context():
        PersistentIdentifier.create('doi', '10.1234/foo')
        assert PersistentIdentifier.get('doi', '10.1234/foo')
        pytest.raises(
            PIDDoesNotExistError,
            PersistentIdentifier.get,
            'doi', '10.1234/bar'
        )

        # PID with provider
        doi = '10.1234/a'
        PersistentIdentifier.create('doi', doi, pid_provider='dcite')
        assert PersistentIdentifier.get('doi', doi)
        assert PersistentIdentifier.get(
            'doi', doi, pid_provider='dcite')
        pytest.raises(
            PIDDoesNotExistError,
            PersistentIdentifier.get,
            'doi', doi, pid_provider='cref'
        )

        # Retrieve by object
        myuuid = uuid.uuid4()
        doi = '10.1234/b'
        PersistentIdentifier.create(
            'doi', doi, object_type='rec', object_uuid=myuuid)
        pid = PersistentIdentifier.get_by_object('doi', 'rec', myuuid)
        assert pid.pid_value == doi

        pytest.raises(
            PIDDoesNotExistError,
            PersistentIdentifier.get_by_object,
            'doi', 'rec', uuid.uuid4()
        )


@patch('invenio_pidstore.models.logger')
def test_pid_assign(logger, app):
    """Test pid object assignment."""
    with app.app_context():
        # No assigned object
        pid = PersistentIdentifier.create('doi', '10.1234/foo')
        assert not pid.has_object()
        assert pid.get_assigned_object() is None
        assert pid.get_assigned_object('rec') is None

        # Assign object
        rec_uuid = uuid.uuid4()
        pid.assign('rec', rec_uuid)
        assert logger.info.call_args[0][0].startswith("Assigned")
        assert 'pid' in logger.info.call_args[1]['extra']
        assert pid.has_object()
        assert pid.get_assigned_object() == rec_uuid
        assert pid.get_assigned_object('rec') == rec_uuid
        assert pid.get_assigned_object('oth') is None
        # Doesnt' raise
        pid.assign('rec', rec_uuid)

        # Assign without overwrite (uuid as str and uuid)
        new_uuid = uuid.uuid4()
        pytest.raises(PIDObjectAlreadyAssigned, pid.assign, 'rec', new_uuid)
        pytest.raises(
            PIDObjectAlreadyAssigned, pid.assign, 'rec', str(new_uuid))

        # Assign with overwrite
        pid.assign('rec', str(new_uuid), overwrite=True)
        assert pid.has_object()
        assert pid.get_assigned_object() == new_uuid
        assert pid.get_assigned_object('rec') == new_uuid
        assert pid.get_assigned_object('oth') is None

        # Assign with SQLError
        pid = PersistentIdentifier.create('recid', '101')
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.assign, 'rec', uuid.uuid4())


@patch('invenio_pidstore.models.logger')
def test_pid_unassign_noobject(logger, app):
    """Test unassign."""
    with app.app_context():
        pid = PersistentIdentifier.create('recid', '101')
        assert pid.unassign()
        pid.assign('rec', uuid.uuid4())
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.unassign)
            assert logger.exception.call_args[0][0].startswith(
                "Failed to unassign")
            assert 'pid' in logger.exception.call_args[1]['extra']


def test_pid_assign_deleted(app):
    """Test pid object assignment."""
    with app.app_context():
        pid = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.DELETED)
        pytest.raises(PIDInvalidAction, pid.assign, 'rec', uuid.uuid4())


@patch('invenio_pidstore.models.logger')
def test_reserve(logger, app):
    """Test pid reserve."""
    with app.app_context():
        i = 1
        for s in [PIDStatus.NEW, PIDStatus.RESERVED]:
            pid = PersistentIdentifier.create('rec', str(i), status=s)
            i += 1
            assert pid.reserve()
            assert logger.info.call_args[0][0].startswith(
                "Reserved PID")
        for s in [PIDStatus.REGISTERED, PIDStatus.DELETED,
                  PIDStatus.REDIRECTED]:
            pid = PersistentIdentifier.create('rec', str(i), status=s)
            i += 1
            pytest.raises(PIDInvalidAction, pid.reserve)

        # Test logging of bad errors.
        pid = PersistentIdentifier.create('rec', str(i))
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.reserve)
            assert logger.exception.call_args[0][0].startswith(
                "Failed to reserve")
            assert 'pid' in logger.exception.call_args[1]['extra']


@patch('invenio_pidstore.models.logger')
def test_register(logger, app):
    """Test pid register."""
    with app.app_context():
        i = 1
        for s in [PIDStatus.NEW, PIDStatus.RESERVED]:
            pid = PersistentIdentifier.create('rec', str(i), status=s)
            i += 1
            assert pid.register()
            assert logger.info.call_args[0][0].startswith(
                "Registered PID")
        for s in [PIDStatus.REGISTERED, PIDStatus.DELETED,
                  PIDStatus.REDIRECTED]:
            pid = PersistentIdentifier.create('rec', str(i), status=s)
            i += 1
            pytest.raises(PIDInvalidAction, pid.register)

        # Test logging of bad errors.
        pid = PersistentIdentifier.create('rec', str(i),
                                          status=PIDStatus.RESERVED)
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.register)
            assert logger.exception.call_args[0][0].startswith(
                "Failed to register")
            assert 'pid' in logger.exception.call_args[1]['extra']


@patch('invenio_pidstore.models.logger')
def test_delete(logger, app):
    """Test pid delete."""
    with app.app_context():
        i = 1
        for s in [PIDStatus.RESERVED, PIDStatus.RESERVED,
                  PIDStatus.REDIRECTED, PIDStatus.DELETED]:
            pid = PersistentIdentifier.create('rec', str(i), status=s)
            i += 1
            assert pid.delete()
            assert logger.info.call_args[0][0] == "Deleted PID."

        # New persistent identifiers are removed completely
        count = PersistentIdentifier.query.count()
        pid = PersistentIdentifier.create('rec', str(i), status=PIDStatus.NEW)
        db.session.commit()
        assert PersistentIdentifier.query.count() == count + 1
        pid.delete()
        assert PersistentIdentifier.query.count() == count
        assert logger.info.call_args[0][0] == "Deleted PID (removed)."

        pid = PersistentIdentifier.create('rec', str(i+1))
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.delete)
            assert logger.exception.call_args[0][0].startswith(
                "Failed to delete")
            assert 'pid' in logger.exception.call_args[1]['extra']


@patch('invenio_pidstore.models.logger')
def test_redirect(logger, app):
    """Test redirection."""
    with app.app_context():
        pid1 = PersistentIdentifier.create(
            'rec', '1', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=uuid.uuid4())
        pid2 = PersistentIdentifier.create(
            'doi', '2', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=uuid.uuid4())

        # Can't redirect these statuses
        i = 10
        for s in [PIDStatus.NEW, PIDStatus.RESERVED, PIDStatus.DELETED, ]:
                pid = PersistentIdentifier.create('rec', str(i), status=s)
                i += 1
                pytest.raises(PIDInvalidAction, pid.redirect, pid1)

        pid = PersistentIdentifier.create(
            'rec', str(i), status=PIDStatus.REGISTERED)

        # Can't redirect to non-exsting pid.
        pytest.raises(PIDDoesNotExistError, pid.redirect,
                      PersistentIdentifier())

        pid.redirect(pid1)
        assert logger.info.call_args[0][0].startswith("Redirected")
        assert 'pid' in logger.info.call_args[1]['extra']
        assert pid.status == PIDStatus.REDIRECTED
        assert pid.object_type is None
        assert pid.object_uuid is not None
        new_pid = pid.get_redirect()
        assert new_pid.pid_type == 'rec'
        assert new_pid.pid_value == '1'

        # You can redirect an already redirected pid
        pid.redirect(pid2)
        new_pid = pid.get_redirect()
        assert new_pid.pid_type == 'doi'
        assert new_pid.pid_value == '2'

        # Assign with SQLError
        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.redirect, '1')
            assert logger.exception.call_args[0][0].startswith(
                "Failed to redirect")
            assert 'pid' in logger.exception.call_args[1]['extra']


def test_redirect_cleanup(app):
    """Test proper clean up from redirects."""
    with app.app_context():
        pid1 = PersistentIdentifier.create(
            'recid', '1', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=uuid.uuid4())
        pid2 = PersistentIdentifier.create(
            'recid', '2', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=uuid.uuid4())
        pid3 = PersistentIdentifier.create(
            'recid', '3', status=PIDStatus.REGISTERED)
        db.session.commit()

        assert Redirect.query.count() == 0
        pid3.redirect(pid1)
        assert Redirect.query.count() == 1
        pid3.redirect(pid2)
        assert Redirect.query.count() == 1
        pytest.raises(
            PIDObjectAlreadyAssigned, pid3.assign, 'rec', uuid.uuid4())
        pid3.unassign()
        assert Redirect.query.count() == 0


@patch('invenio_pidstore.models.logger')
def test_sync_status(logger, app):
    """Test sync status."""
    with app.app_context():
        pid = PersistentIdentifier.create(
            'rec', '1', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid=uuid.uuid4())
        pytest.raises(PIDInvalidAction, pid.reserve)
        calls = logger.info.call_count
        assert pid.sync_status(PIDStatus.NEW)
        assert logger.info.call_count == calls + 1
        assert pid.reserve()
        calls = logger.info.call_count
        assert pid.sync_status(PIDStatus.RESERVED)
        assert logger.info.call_count == calls

        with patch('invenio_pidstore.models.db.session.begin_nested') as mock:
            mock.side_effect = SQLAlchemyError()
            pytest.raises(SQLAlchemyError, pid.sync_status, PIDStatus.NEW)
            assert logger.exception.call_args[0][0].startswith(
                "Failed to sync status")
            assert 'pid' in logger.exception.call_args[1]['extra']


def test_repr(app):
    """Test representation."""
    with app.app_context():
        pid = PersistentIdentifier.create(
            'recid', '1', status=PIDStatus.REGISTERED, object_type='rec',
            object_uuid='de3bb351-bc1a-4e51-8605-c6cd9589a560')
        assert str(pid) == \
            "<PersistentIdentifier recid:1 / " \
            "rec:de3bb351-bc1a-4e51-8605-c6cd9589a560 (R)>"
        pid = PersistentIdentifier.create(
            'recid', '2', status=PIDStatus.REGISTERED)
        assert str(pid) == "<PersistentIdentifier recid:2 (R)>"
