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
        # import ipdb; ipdb.set_trace()
        pidlog0a, pidlog0b = PidLog.query.all()[-2:]
        assert pidlog0a.action == 'CREATE'
        assert pidlog0a.message == '[mock_t:pid_val0] Created'
        assert pidlog0a.id_pid is None

        assert pidlog0b.action == 'DELETE'
        assert pidlog0b.message == \
            '[mock_t:pid_val0] Unregistered PID successfully deleted'
        assert pidlog0b.id_pid is None


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

        # Note: It is possible that the lines models.py:L241-243
        # have no real entry point through API methods
        pid1 = PersistentIdentifier.create('mock_t', 'pid_val1', 'pid_provi1')
        pid1.register()
        # Manually change properties
        pid1._provider = None
        pid1.pid_type = 'foo_t'
        with pytest.raises(Exception) as exc_info:
            pid1.update()
        assert exc_info.exconly() == \
            'Exception: No provider found.'


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
