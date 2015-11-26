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

"""Provider tests."""

from __future__ import absolute_import, print_function

import uuid

import pytest
from datacite.errors import DataCiteError, DataCiteGoneError, \
    DataCiteNoContentError, DataCiteNotFoundError, HttpError
from mock import MagicMock, patch

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider
from invenio_pidstore.providers.datacite import DataCiteProvider
from invenio_pidstore.providers.recordid import RecordIdProvider


def test_base_provider(app):
    """Test base provider."""
    with app.app_context():
        provider = BaseProvider.create(pid_type='test', pid_value='test')
        assert provider.pid
        assert provider.pid.pid_type == 'test'
        assert provider.pid.pid_value == 'test'
        assert provider.pid.pid_provider is None
        assert provider.pid.status == PIDStatus.NEW
        assert provider.pid.object_type is None
        assert provider.pid.object_uuid is None

        provider.reserve()
        assert provider.pid.is_reserved()

        provider.register()
        assert provider.pid.is_registered()

        provider.delete()
        assert provider.pid.is_deleted()

        provider.sync_status()
        provider.update()

    class TestProvider(BaseProvider):
        pid_type = 't'
        pid_provider = 'testpr'
        default_status = PIDStatus.RESERVED

    with app.app_context():
        provider = TestProvider.create(pid_value='test')
        assert provider.pid
        assert provider.pid.pid_type == 't'
        assert provider.pid.pid_provider == 'testpr'
        assert provider.pid.pid_value == 'test'
        assert provider.pid.status == PIDStatus.RESERVED

        assert TestProvider.get('test')


def test_recordid_provider(app):
    """Test record id provider."""
    with app.app_context():
        provider = RecordIdProvider.create()
        assert provider.pid
        assert provider.pid.pid_type == 'recid'
        assert provider.pid.pid_value == '1'
        assert provider.pid.pid_provider is None
        assert provider.pid.status == PIDStatus.RESERVED
        assert provider.pid.object_type is None
        assert provider.pid.object_uuid is None

        # Assign to object immediately
        rec_uuid = uuid.uuid4()
        provider = RecordIdProvider.create(
            object_type='rec', object_uuid=rec_uuid)
        assert provider.pid
        assert provider.pid.pid_type == 'recid'
        assert provider.pid.pid_value == '2'
        assert provider.pid.pid_provider is None
        assert provider.pid.status == PIDStatus.REGISTERED
        assert provider.pid.object_type == 'rec'
        assert provider.pid.object_uuid == rec_uuid

        pytest.raises(AssertionError, RecordIdProvider.create, pid_value='3')


def test_datacite_create_get(app):
    """Test datacite provider create/get."""
    with app.app_context():
        provider = DataCiteProvider.create('10.1234/a')
        assert provider.pid.status == PIDStatus.NEW
        assert provider.pid.pid_provider == 'datacite'

        # Crete passing client kwarg to provider object creation
        provider = DataCiteProvider.create('10.1234/b', client=MagicMock())
        assert provider.pid.status == PIDStatus.NEW
        assert provider.pid.pid_provider == 'datacite'
        assert isinstance(provider.api, MagicMock)

        provider = DataCiteProvider.get('10.1234/a')
        assert provider.pid.status == PIDStatus.NEW
        assert provider.pid.pid_provider == 'datacite'

        provider = DataCiteProvider.get('10.1234/a', client=MagicMock())
        assert isinstance(provider.api, MagicMock)


def test_datacite_reserve_register_update_delete(app):
    """Test datacite provider reserve."""
    with app.app_context():
        api = MagicMock()
        provider = DataCiteProvider.create('10.1234/a', client=api)
        assert provider.reserve('mydoc')
        assert provider.pid.status == PIDStatus.RESERVED
        api.metadata_post.assert_called_with('mydoc')

        assert provider.register('myurl', 'anotherdoc')
        assert provider.pid.status == PIDStatus.REGISTERED
        api.metadata_post.assert_called_with('anotherdoc')
        api.doi_post.assert_called_with('10.1234/a', 'myurl')

        assert provider.update('anotherurl', 'yetanother')
        assert provider.pid.status == PIDStatus.REGISTERED
        api.metadata_post.assert_called_with('yetanother')
        api.doi_post.assert_called_with('10.1234/a', 'anotherurl')

        assert provider.delete()
        assert provider.pid.status == PIDStatus.DELETED
        api.metadata_delete.assert_called_with('10.1234/a')

        assert provider.update('newurl', 'newdoc')
        assert provider.pid.status == PIDStatus.REGISTERED
        api.metadata_post.assert_called_with('newdoc')
        api.doi_post.assert_called_with('10.1234/a', 'newurl')


@patch('invenio_pidstore.providers.datacite.logger')
def test_datacite_error_reserve(logger, app):
    """Test reserve errors."""
    with app.app_context():
        api = MagicMock()
        provider = DataCiteProvider.create('10.1234/a', client=api)

        api.metadata_post.side_effect = DataCiteError
        pytest.raises(DataCiteError, provider.reserve, "testdoc")
        assert logger.exception.call_args[0][0] == \
            "Failed to reserve in DataCite"


@patch('invenio_pidstore.providers.datacite.logger')
def test_datacite_error_register_update(logger, app):
    """Test register errors."""
    with app.app_context():
        api = MagicMock()
        provider = DataCiteProvider.create('10.1234/a', client=api)

        api.doi_post.side_effect = DataCiteError
        pytest.raises(DataCiteError, provider.register, "testurl", "testdoc")
        assert logger.exception.call_args[0][0] == \
            "Failed to register in DataCite"

        pytest.raises(DataCiteError, provider.update, "testurl", "testdoc")
        assert logger.exception.call_args[0][0] == \
            "Failed to update in DataCite"


@patch('invenio_pidstore.providers.datacite.logger')
def test_datacite_error_delete(logger, app):
    """Test reserve errors."""
    with app.app_context():
        api = MagicMock()
        provider = DataCiteProvider.create('10.1234/a', client=api)

        # DOIs in new state doesn't contact datacite
        api.metadata_delete.side_effect = DataCiteError
        assert provider.delete()

        # Already registered DOIs do contact datacite to delete
        provider = DataCiteProvider.create('10.1234/b', client=api,
                                           status=PIDStatus.REGISTERED)

        api.metadata_delete.side_effect = DataCiteError
        pytest.raises(DataCiteError, provider.delete)
        assert logger.exception.call_args[0][0] == \
            "Failed to delete in DataCite"


@patch('invenio_pidstore.providers.datacite.logger')
def test_datacite_sync(logger, app):
    """Test sync."""
    with app.app_context():
        api = MagicMock()

        provider = DataCiteProvider.create('10.1234/a', client=api)
        assert provider.pid.status == PIDStatus.NEW

        # Status can be set from api.doi_get reply
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.REGISTERED
        api.doi_get.assert_called_with(provider.pid.pid_value)

        api.doi_get.side_effect = DataCiteGoneError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.DELETED

        api.doi_get.side_effect = DataCiteNoContentError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.REGISTERED

        # Status *cannot/ be set from api.doi_get reply
        # Try with api.metadata_get
        api.doi_get.side_effect = DataCiteNotFoundError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.RESERVED
        api.metadata_get.assert_called_with(provider.pid.pid_value)

        api.doi_get.side_effect = DataCiteNotFoundError
        api.metadata_get.side_effect = DataCiteGoneError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.DELETED

        api.doi_get.side_effect = DataCiteNotFoundError
        api.metadata_get.side_effect = DataCiteNoContentError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.REGISTERED

        api.doi_get.side_effect = DataCiteNotFoundError
        api.metadata_get.side_effect = DataCiteNotFoundError
        assert provider.sync_status()
        assert provider.pid.status == PIDStatus.NEW

        api.doi_get.side_effect = HttpError
        assert provider.pid.status == PIDStatus.NEW
        pytest.raises(HttpError, provider.sync_status)
        assert provider.pid.status == PIDStatus.NEW
        assert logger.exception.call_args[0][0] == \
            "Failed to sync status from DataCite"
