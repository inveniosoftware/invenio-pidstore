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


"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask
from invenio_db import db

from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PidLog
from invenio_pidstore.provider import PidProvider, PIDStatus
from invenio_pidstore.registry import _collect_pidproviders


def test_version():
    """Test version import."""
    from invenio_pidstore import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioPIDStore(app)
    assert 'invenio-pidstore' in app.extensions

    app = Flask('testapp')
    ext = InvenioPIDStore()
    assert 'invenio-pidstore' not in app.extensions
    ext.init_app(app)
    assert 'invenio-pidstore' in app.extensions


def test_pid_model_class_methods(app):
    """Test the class methods of PersistentIdentifier class."""
    with app.app_context():
        # Class methods tests
        # Create one PID (and one PidLog entry)
        assert PersistentIdentifier.query.count() == 0
        assert PidLog.query.count() == 0
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert PersistentIdentifier.query.count() == 1
        assert PidLog.query.count() == 1

        # Check if PidLog entry matches PID
        pidlog0 = PidLog.query.first()
        assert pidlog0.action == 'CREATE'
        assert pidlog0.message == '[mock_t:pid_val0] Created'
        assert pidlog0.id_pid == pid0.id

        # Get the same PID as before (and make sure it is the one)
        pid1 = PersistentIdentifier.get('mock_t', 'pid_val0', 'pid_provi0')
        assert (pid1 == pid0) and (pid1 is not None)

        # Create the same PID (should fail)
        pid2 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert pid2 is None
        pidlog1 = PidLog.query.all()[-1]
        assert pidlog1.message == \
            '[mock_t:pid_val0] Failed to create. Already exists.'

        # Try to create PID with unknown type
        with pytest.raises(Exception) as exc_info:
            pid3 = PersistentIdentifier.create('new_type', 'foo', 'bar')
            assert pid3 is None
        assert exc_info.exconly() == \
            'Exception: No provider found for new_type:foo (bar)'

        # Get a non-existent PID
        pid4 = PersistentIdentifier.get('foo', 'bar', 'baz')
        assert pid4 is None


def test_pid_model_instance_methods(app):
    """Test general instance methods of the PersistentIdentifier class."""
    with app.app_context():
        # Try to get not yet assigned object
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert not pid0.has_object('rec', 'obj_val0')

        # Try to assign object with wrong type
        with pytest.raises(Exception) as exc_info:
            pid0.assign('non_existent_type', 'obj_val0')
        assert exc_info.exconly() == \
            'Exception: Invalid object type non_existent_type.'

        # Assign object with existing type and test if it's there
        pid0.assign('rec', 'obj_val0')
        assert not pid0.has_object('rec', 'wrong_obj_val')
        assert pid0.has_object('rec', 'obj_val0')

        # Assign again the same object, should not change anything
        assert pid0.assign('rec', 'obj_val0')
        assert pid0.has_object('rec', 'obj_val0')

        # Try to get object with non existent type
        with pytest.raises(Exception) as exc_info:
            assert not pid0.has_object('non_existent_type', 'obj_val0')
        assert exc_info.exconly() == \
            'Exception: Invalid object type non_existent_type.'

        # Try to assign new object in place of old one without overwrite flag
        with pytest.raises(Exception) as exc_info:
            pid0.assign('rec', 'obj_val1')
        assert exc_info.exconly() == 'Exception: Persistent identifier ' \
            'is already assigned to another object'

        pid0.assign('rec', 'obj_val1', overwrite=True)
        db.session.commit()
        pidlog0 = PidLog.query.all()[-2]
        assert pidlog0.message == \
            '[mock_t:pid_val0] Unassigned object rec:obj_val0 ' \
            '(overwrite requested)'

        pidlog0 = PidLog.query.all()[-1]
        assert pidlog0.message == \
            '[mock_t:pid_val0] Assigned object rec:obj_val1'

        # Get provider and make sure it's of the correct pid_type
        provider = pid0.get_provider()
        assert isinstance(provider, PidProvider)
        assert provider.pid_type == 'mock_t'

        # Try to get missing provider from hand made ORM object
        pid = PersistentIdentifier(pid_type='mock_t',
                                   pid_value='pid_val2',
                                   pid_provider='pid_prov_2',
                                   status=PIDStatus.NEW)
        db.session.add(pid)
        db.session.commit()
        pid = PersistentIdentifier.get('mock_t', 'pid_val2', 'pid_prov_2')
        assert pid.get_provider() is not None
        assert isinstance(pid.get_provider(), PidProvider)
        assert pid.get_provider().pid_type == 'mock_t'


def test_pid_model_provider(app):
    """Test the provider-related queries."""
    with app.app_context():

        # Reserve method
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert pid0.is_new()
        assert pid0.reserve()
        assert pid0.is_reserved()
        # Should be able to call the method multiple times
        assert pid0.reserve()
        assert pid0.is_reserved()

        assert pid0.register()
        with pytest.raises(Exception) as exc_info:
            assert not pid0.reserve()  # Can not reserve after register
        assert exc_info.exconly() == \
            'Exception: Persistent identifier has already been registered.'
        db.session.commit()

        with pytest.raises(Exception) as exc_info:
            assert not pid0.register()  # Can not register twice
        assert exc_info.exconly() == \
            'Exception: Persistent identifier has already been registered.'
        db.session.commit()

        # Register method
        pid1 = PersistentIdentifier.create('mock_t', 'pid_val1', 'pid_provi1')
        assert pid1.register()

        # Update method
        pid2 = PersistentIdentifier.create('mock_t', 'pid_val2', 'pid_provi2')

        # Trying to update a PID with status NEW should raise an error
        assert pid2.is_new()
        with pytest.raises(Exception) as exc_info:
            pid2.update()
        assert exc_info.exconly() == \
            'Exception: Persistent identifier has not yet been registered.'

        assert pid2.reserve()  # Reserve it
        assert pid2.is_reserved()
        with pytest.raises(Exception) as exc_info:
            pid2.update()  # Should still refuse to update
        assert exc_info.exconly() == \
            'Exception: Persistent identifier has not yet been registered.'

        assert pid2.register()  # Reserve it
        assert pid2.is_registered()
        assert pid2.update()  # Update it


def test_model_pid_delete(app):
    """Test PID delete method."""
    with app.app_context():
        # Delete the object before registering, should still exist
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert pid0.delete()  # Remove the item from the database
        assert PersistentIdentifier.query.count() == 0  # DB should be empty
        assert PidLog.query.count() == 2  # Log entry should remain in DB
        log0c, log0d = PidLog.query.all()
        assert log0c.action == 'CREATE'
        assert log0c.message == '[mock_t:pid_val0] Created'
        assert log0d.message == \
            '[mock_t:pid_val0] Unregistered PID successfully deleted'

        # Create another object
        pid1 = PersistentIdentifier.create('mock_t', 'pid_val1', 'pid_provi1')
        pid1.register()  # This time register it with provider
        assert pid1.delete()  # Remove the item from the database
        assert PersistentIdentifier.query.count() == 1  # It should stay in DB
        assert PidLog.query.count() == 3  # Only one extra CREATE entry
        log1c = PidLog.query.all()[-1]
        assert log1c.message == '[mock_t:pid_val1] Created'


def test_model_pid_delete_new(app):
    """Test PID delete method on PID with status NEW ."""
    with app.app_context():
        # Last two logs should be from creating and then from deleting the PID
        # Both should not reference any PID anymore
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        assert pid0.is_new()
        assert pid0.delete()
        pidlog0a, pidlog0b = PidLog.query.all()[-2:]
        assert pidlog0a.action == 'CREATE'
        assert pidlog0a.message == '[mock_t:pid_val0] Created'
        assert pidlog0a.id_pid is None

        assert pidlog0b.action == 'DELETE'
        assert pidlog0b.message == \
            '[mock_t:pid_val0] Unregistered PID successfully deleted'
        assert pidlog0b.id_pid is None


def test_model_pid_reserve_provider_not_found(app):
    """
    Corner-case for the test PID reserve method.

    This test covers the raising of the Exception('No provider found') in the
    'PersistentIdentifier.reserve' method
    """
    with app.app_context():
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        pid0._provider = None
        pid0.pid_type = 'foo_t'
        with pytest.raises(Exception) as exc_info:
            pid0.reserve()
        assert exc_info.exconly() == \
            'Exception: No provider found.'
        log0 = PidLog.query.all()[-1]
        assert log0.action == 'RESERVE'
        assert log0.message == '[foo_t:pid_val0] No provider found.'


def test_model_pid_update(app):
    """Test PID update method."""
    with app.app_context():
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        pid0.register()
        assert pid0.delete()  # Remove the item from the database

        # Try to update deleted PID without 'with_delted' flag
        with pytest.raises(Exception) as exc_info:
            assert pid0.update()
        assert exc_info.exconly() == \
            'Exception: Persistent identifier has been deleted.'

        # Try to update deleted PID with 'with_deleted' flag.
        assert pid0.is_deleted()
        assert pid0.update(with_deleted=True)
        assert pid0.is_registered()  # It should change status to REGISTERED


def test_model_pid_update_provider_not_found(app):
    """
    Corner case for the Test PID update method.

    This test covers the raising of the Exception('No provider found') in the
    'PersistentIdentifier.update' method. It is very possible that this
    scenario has no real entry point through API methods.
    """
    with app.app_context():
        pid1 = PersistentIdentifier.create('mock_t', 'pid_val1', 'pid_provi1')
        pid1.register()
        # Manually change properties
        pid1._provider = None
        pid1.pid_type = 'foo_t'
        with pytest.raises(Exception) as exc_info:
            pid1.update()
        assert exc_info.exconly() == \
            'Exception: No provider found.'
        log1 = PidLog.query.all()[-1]
        assert log1.action == 'UPDATE'
        assert log1.message == '[foo_t:pid_val1] No provider found.'


def test_model_pid_register_provider_not_found(app):
    """
    Corner-case for the test PID register method.

    This test covers the raising of the Exception('No provider found') in the
    'PersistentIdentifier.register' method
    """
    with app.app_context():
        pid0 = PersistentIdentifier.create('mock_t', 'pid_val0', 'pid_provi0')
        pid0._provider = None
        pid0.pid_type = 'foo_t'
        with pytest.raises(Exception) as exc_info:
            pid0.register()
        assert exc_info.exconly() == \
            'Exception: No provider found.'
        log0 = PidLog.query.all()[-1]
        assert log0.action == 'REGISTER'
        assert log0.message == '[foo_t:pid_val0] No provider found.'


def test_model_pid_assign(app):
    """Test PID assign method."""
    with app.app_context():
        # Call the assign method without on PID without ID
        pid0 = PersistentIdentifier(pid_type='mock_t',
                                    pid_value='pid_val5',
                                    pid_provider='pid_prov_5',
                                    status=PIDStatus.NEW)
        with pytest.raises(Exception) as exc_info:
            pid0.assign('rec', 'obj_val5')
        assert exc_info.exconly() == \
            "Exception: You must first create the persistent identifier " \
            "before you can assign objects to it."

        # Call the assign method on deleted PID
        pid1 = PersistentIdentifier.create('mock_t', 'pid_val6', 'pid_provi6')
        db.session.commit()
        pid1.register()
        pid1.delete()
        db.session.commit()
        assert pid1.is_deleted()
        with pytest.raises(Exception) as exc_info:
            pid1.assign('rec', 'obj_val6')
        assert exc_info.exconly() == \
            "Exception: You cannot assign objects to a deleted " \
            "persistent identifier."


def test_template_filters(app):
    """Test the template filters."""
    with app.app_context():
        # Test the 'pid_exists' template filter
        pid_exists = app.jinja_env.filters['pid_exists']
        assert not pid_exists('pid_val0', pidtype='mock_t')
        PersistentIdentifier.create('mock_t', 'pid_val0', '')
        db.session.commit()
        assert pid_exists('pid_val0', pidtype='mock_t')
        assert not pid_exists('foo', pidtype='mock_t')
        assert not pid_exists('pid_val0', pidtype='foo')


class MockDataCiteMDSClient(object):
    """Mock of the datacite.DataCiteMDSClient class."""

    def __init__(self):
        """Init the DataCiteMDSClass with connection config."""
        # Testing environment should set these to simulate failing
        self.METADATA_POST_RAISE = None
        self.METADATA_GET_RAISE = None
        self.METADATA_DELETE_RAISE = None
        self.DOI_GET_RAISE = None

    def metadata_post(self, doc):
        """
        Metadata post method mock.

        Depending on the value of self.METADATA_POST_RAISE can raise errors.
        """
        if self.METADATA_POST_RAISE is not None:
            raise self.METADATA_POST_RAISE("POST_ERROR_MSG")

    def metadata_get(self, doc):
        """
        Metadata get method mock.

        Depending on the value of self.METADATA_GET_RAISE can raise errors.
        """
        if self.METADATA_GET_RAISE is not None:
            raise self.METADATA_GET_RAISE("GET_ERROR_MSG")

    def metadata_delete(self, doc):
        """
        Metadata delete method mock.

        Depending on the value of self.METADATA_DELETE_RAISE can raise errors.
        """
        if self.METADATA_DELETE_RAISE is not None:
            raise self.METADATA_DELETE_RAISE("DELETE_ERROR_MSG")

    def doi_get(self, pid_value):
        """
        DOI get method.

        Depending on the value of self.DOI_GET_RAISE can raise errors.
        """
        if self.DOI_GET_RAISE is not None:
            raise self.DOI_GET_RAISE("DOI_GET_ERROR_MSG")

    def doi_post(self, pid_value, url):
        """DOI post method mock."""
        pass


def test_mocking_datacite_and_local_doi(app):
    """
    Test the datacite and local PID providers.

    This long test simulates the lifetime of a single PID, testing the API
    in the following order:
    create -> reserve -> register -> update -> delete -> update -> sync_status
    And simulate various error raising on DataCite side.
    The second 'update' is repeated to test the behaviour on a deleted PID.
    """
    from datacite.errors import DataCiteError, DataCiteGoneError, \
        DataCiteNoContentError, DataCiteNotFoundError, HttpError

    # This config variable is usually provided from the environment
    app.config['PIDSTORE_DATACITE_DOI_PREFIX'] = 'doi_datacite'

    # Test the lifetime of DataCite PID
    with app.app_context():
        from invenio_pidstore.providers.datacite import DataCite
        from invenio_pidstore.providers.local_doi import LocalDOI

        # Create new PID:
        # PID with type 'doi' and correct doi_value with a DataCite
        # prefix (for the purpose of the test set as 'doi_datacite/',
        # see conftest.py) should return DataCite provider.
        pid_dc = PersistentIdentifier.create(pid_type='doi',
                                             pid_value='doi_datacite/0001',
                                             pid_provider='datacite')
        assert isinstance(pid_dc._provider, DataCite)

        pid_dc._provider.api = MockDataCiteMDSClient()
        pid_dc_api = pid_dc._provider.api

        # Reserve the PID:
        # Call 'reserve' without 'doc' kwarg
        with pytest.raises(Exception) as exc_info:
            pid_dc.reserve()
        assert pid_dc.is_new()  # PIDStatus should remain 'NEW'
        assert exc_info.exconly() == \
            "Exception: doc keyword argument must be specified."

        # Call 'reserve' and simulate DataCiteError
        pid_dc_api.METADATA_POST_RAISE = DataCiteError  # Enable DataCiteError
        assert not pid_dc.reserve(doc='some doc')  # Shoulr return 'False'
        assert pid_dc.is_new()  # PIDStatus should remain 'NEW'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "RESERVE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'reserve' and simulate HttpError
        pid_dc_api.METADATA_POST_RAISE = HttpError  # Enable HttpError
        assert not pid_dc.reserve(doc='some doc')  # Should return 'False'
        assert pid_dc.is_new()  # PIDStatus should remain 'NEW'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "RESERVE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - POST_ERROR_MSG'

        # Call 'reserve' with success on DataCite side
        pid_dc_api.METADATA_POST_RAISE = None  # Disable error raising
        assert pid_dc.reserve(doc='some doc')  # Should return 'True'
        assert pid_dc.is_reserved()  # PIDStatus should change to 'RESERVED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "RESERVE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Successfully reserved in DataCite'

        # Register the PID:
        # Call 'register' without 'url' kwarg
        with pytest.raises(Exception) as exc_info:
            pid_dc.register(doc='some_doc')
        assert pid_dc.is_reserved()  # PIDStatus should remain 'RESERVED'
        assert exc_info.exconly() == \
            "Exception: url keyword argument must be specified."

        # Call 'register' and simulate DataCiteError
        pid_dc_api.METADATA_POST_RAISE = DataCiteError  # Enable DataCiteError
        assert not pid_dc.register(doc='d', url='u')  # Should return 'False'
        assert pid_dc.is_reserved()  # PIDStatus should remain 'RESERVED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "REGISTER"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'register' and simulate HttpError
        pid_dc_api.METADATA_POST_RAISE = HttpError  # Enable HttpError
        assert not pid_dc.register(doc='d', url='u')  # Should return 'False'
        assert pid_dc.is_reserved()  # PIDStatus should remain 'RESERVED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "REGISTER"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - POST_ERROR_MSG'

        # Call 'register' with success on DataCite side
        pid_dc_api.METADATA_POST_RAISE = None  # Disable error raising
        assert pid_dc.register(doc='d', url='u')  # Should return 'True'
        assert pid_dc.is_registered()  # PIDStatus change to 'REGISTERED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "REGISTER"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Successfully registered in DataCite'

        # Update the PID:
        # Call 'update' and simulate DataCiteError
        pid_dc_api.METADATA_POST_RAISE = DataCiteError  # Enable DataCiteError
        assert not pid_dc.update(doc='d', url='u')  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "UPDATE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'update' and simulate HttpError
        pid_dc_api.METADATA_POST_RAISE = HttpError  # Enable DataCiteError
        assert not pid_dc.update(doc='d', url='u')  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "UPDATE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - POST_ERROR_MSG'

        # Call 'update' with success on DataCite side
        pid_dc_api.METADATA_POST_RAISE = None  # Disable error raising
        assert pid_dc.update(doc='d', url='u')  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "UPDATE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Successfully updated in DataCite'

        # Delete the PID:
        # Call 'delete' and simulate DataCiteError
        pid_dc_api.METADATA_DELETE_RAISE = DataCiteError  # Enable error
        assert not pid_dc.delete()  # Should return 'False'
        assert pid_dc.is_registered()  # PIDStatus remains 'REGISTERED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "DELETE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'delete' and simulate HttpError
        pid_dc_api.METADATA_DELETE_RAISE = HttpError  # Enable error
        assert not pid_dc.delete()  # Should return 'False'
        assert pid_dc.is_registered()  # PIDStatus remains 'REGISTERED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "DELETE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - DELETE_ERROR_MSG'

        # Call 'delete' successfully on DataCiteSide
        pid_dc_api.METADATA_DELETE_RAISE = None  # Disable error
        assert pid_dc.delete()  # Should return 'True'
        assert pid_dc.is_deleted()  # PIDStatus changed to 'DELETED'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "DELETE"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Successfully deleted in DataCite'

        # Update the deleted PID:
        # Call 'update' with success on DataCite side
        pid_dc_api.METADATA_POST_RAISE = None  # Disable error raising
        assert pid_dc.update(with_deleted=True, doc='d', url='u')
        # Last two PidLog entries should come from the update method
        pidlog1, pidlog2 = PidLog.query.all()[-2:]
        assert pidlog1.action == "UPDATE"
        assert pidlog1.message == \
            '[doi:doi_datacite/0001] Reactivate in DataCite'
        assert pidlog2.action == "UPDATE"
        assert pidlog2.message == \
            '[doi:doi_datacite/0001] Successfully updated and possibly ' \
            'registered in DataCite'
        assert pid_dc.is_registered()  # Status change to 'REGISTERED'

        # Sync the status with DataCite using 'sync_status':
        # Call 'sync_status' and simulate DataCiteError
        pid_dc_api.DOI_GET_RAISE = DataCiteError  # Enable error
        assert not pid_dc.sync_status()  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'sync_status' and simulate HttpError
        pid_dc_api.DOI_GET_RAISE = HttpError  # Enable error
        assert not pid_dc.sync_status()  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - DOI_GET_ERROR_MSG'

        # Call 'sync_status' and simulate DataCiteGoneError
        pid_dc_api.DOI_GET_RAISE = DataCiteGoneError  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from R to D.'
        assert pid_dc.is_deleted()  # Should change status to DELETED

        # Call 'sync_status' and simulate DataCiteNoContentError
        pid_dc_api.DOI_GET_RAISE = DataCiteNoContentError  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from D to R.'
        assert pid_dc.is_registered()  # Should change status to REGISTERED

        # Call 'sync_status'
        # First simulate no record on DataCite (DataCiteNotFound on
        # the call to api.doi_get) and then various errors on api.metadata_get
        pid_dc_api.DOI_GET_RAISE = DataCiteNotFoundError  # Enable first error

        # Call 'sync_status' with DataCiteError (on api.metadata_get)
        pid_dc_api.METADATA_GET_RAISE = DataCiteError  # Enable second error
        assert not pid_dc.sync_status()  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with DataCiteError'

        # Call 'sync_status' with HttpError (on api.metadata_get)
        pid_dc_api.METADATA_GET_RAISE = HttpError  # Enable error
        assert not pid_dc.sync_status()  # Should return 'False'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Failed with HttpError - GET_ERROR_MSG'

        # Call 'sync_status' with DataCiteGoneError (on api.metadata_get)
        pid_dc_api.METADATA_GET_RAISE = DataCiteGoneError  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from R to D.'
        assert pid_dc.is_deleted()  # Should change status to DELETED

        # Call 'sync_status' with DataCiteNoContentError (on api.metadata_get)
        pid_dc_api.METADATA_GET_RAISE = DataCiteNoContentError  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from D to R.'
        assert pid_dc.is_registered()  # Should change status to REGISTERED

        # Call 'sync_status' with DataCiteNotFoundError (on api.metadata_get)
        pid_dc_api.METADATA_GET_RAISE = DataCiteNotFoundError  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from R to N.'
        assert pid_dc.is_new()  # Should change status to NEW

        # Call 'sync_status' with success on api.metadata_get
        pid_dc_api.METADATA_GET_RAISE = None  # Enable error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from N to K.'
        assert pid_dc.is_reserved()  # Should change status to RESERVED

        # Finally, call 'sync_status' and make it work :)
        pid_dc_api.DOI_GET_RAISE = None  # Disable first error
        pid_dc_api.METADATA_GET_RAISE = None  # Disable second error
        assert pid_dc.sync_status()  # Should return 'True'
        pidlog_last = PidLog.query.all()[-1]
        assert pidlog_last.action == "SYNC"
        assert pidlog_last.message == \
            '[doi:doi_datacite/0001] Fixed status from K to R.'
        assert pid_dc.is_registered()  # Should change status to REGISTERED

    # Test the lifetime of LocalDOI provided PID
    with app.app_context():
        # PID with type 'doi' and non-DataCite prefix should assign a
        # LocalDOI PID provider
        pid_local = PersistentIdentifier.create(pid_type='doi',
                                                pid_value='other_prefix/0001',
                                                pid_provider='localdoi')
        assert isinstance(pid_local._provider, LocalDOI)
        assert pid_local.is_new()  # Should have status NEW

        # Reserve local DOI:
        assert pid_local.reserve()
        assert pid_local.is_reserved()
        pidlog_reserve = PidLog.query.all()[-1]
        assert pidlog_reserve.action == "RESERVE"
        assert pidlog_reserve.message == \
            '[doi:other_prefix/0001] Successfully reserved locally'

        # Register local DOI
        assert pid_local.register()
        assert pid_local.is_registered()
        pidlog_register = PidLog.query.all()[-1]
        assert pidlog_register.action == "REGISTER"
        assert pidlog_register.message == \
            '[doi:other_prefix/0001] Successfully registered locally'

        # Update local DOI
        assert pid_local.update()
        pidlog_last_after_update = PidLog.query.all()[-1]
        assert pidlog_last_after_update == pidlog_register
        # Update does not generate new Log, so last PidLog should be as before

        # Delete local DOI
        assert pid_local.delete()
        assert pid_local.is_deleted()
        pidlog_delete = PidLog.query.all()[-1]
        assert pidlog_delete.action == "DELETE"
        assert pidlog_delete.message == \
            '[doi:other_prefix/0001] Successfully deleted locally'

        # Sync status of local DOI
        assert pid_local.sync_status()


def test_registry_collect_pidproviders(app):
    """Test the collection of pidproviders from the config."""
    with app.app_context():
        config_pidstore_providers_orig = app.config['PIDSTORE_PROVIDERS']
        app.config['PIDSTORE_PROVIDERS'] = \
            ['tests.mock_providers.mock_datacite:MissingPidType', ]
        with pytest.raises(AttributeError) as exc_info:
            _collect_pidproviders()
        assert exc_info.exconly() == \
            'AttributeError: Provider must specify class variable pid_type.'

        app.config['PIDSTORE_PROVIDERS'] = \
            ['tests.mock_providers.mock_datacite:PidProviderNotInheriting', ]
        with pytest.raises(TypeError) as exc_info:
            _collect_pidproviders()
        assert exc_info.exconly() == \
            'TypeError: Argument not an instance of PidProvider.'

        app.config['PIDSTORE_PROVIDERS'] = config_pidstore_providers_orig
