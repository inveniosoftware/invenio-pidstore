# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Minter tests."""

from __future__ import absolute_import, print_function

import uuid

from invenio_pidstore import current_pidstore
from invenio_pidstore.minters import recid_minter


def test_recid_minter(app, db):
    """Test base provider."""
    with app.app_context():

        rec_uuid = uuid.uuid4()
        data = {}
        pid = recid_minter(rec_uuid, data)
        assert pid
        assert data[app.config['PIDSTORE_RECID_FIELD']] == pid.pid_value
        assert pid.object_type == 'rec'
        assert pid.object_uuid == rec_uuid


def test_register_minter(app):
    """Test base provider."""
    with app.app_context():
        current_pidstore.register_minter('anothername', recid_minter)
