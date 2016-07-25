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

"""Persistent identifier minters."""

from __future__ import absolute_import, print_function

from .providers.recordid import RecordIdProvider


def recid_minter(record_uuid, data):
    """Mint record identifiers.

    This is a minter specific for records.
    With the help of
    :class:`invenio_pidstore.providers.recordid.RecordIdProvider`, it creates
    the PID instance with `rec` as predefined `object_type`.

    Procedure followed:

    #. If a `control_number` field is already there, a `AssertionError`
    exception is raised.

    #. The provider is initialized with the help of
    :class:`invenio_pidstore.providers.recordid.RecordIdProvider`.
    It's called with default value 'rec' for `object_type` and `record_uuid`
    variable for `object_uuid`.

    #. The new `id_value` is stored inside `data` as `control_number` field.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :returns: A fresh `invenio_pidstore.models.PersistentIdentifier` instance.
    """
    assert 'control_number' not in data
    provider = RecordIdProvider.create(
        object_type='rec', object_uuid=record_uuid)
    data['control_number'] = provider.pid.pid_value
    return provider.pid
