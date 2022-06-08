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

import pytest

from invenio_pidstore import current_pidstore
from invenio_pidstore.minters import recid_minter, recid_minter_v2


def test_recid_minter(app, db):
    """Test legacy recid minter."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        data = {}

        pid = recid_minter(rec_uuid, data)

        assert pid
        assert data[app.config["PIDSTORE_RECID_FIELD"]] == pid.pid_value
        assert pid.object_type == "rec"
        assert pid.object_uuid == rec_uuid


def test_recid_minter_v2(app, db):
    """Test recommended recid minter."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        data = {}
        recid_field = app.config["PIDSTORE_RECID_FIELD"]

        pid = recid_minter_v2(rec_uuid, data)

        assert pid
        assert data[recid_field] == pid.pid_value
        assert pid.object_type == "rec"
        assert pid.object_uuid == rec_uuid

        with pytest.raises(AssertionError):
            recid_minter_v2(rec_uuid, {recid_field: "1"})


def test_register_minter(app):
    """Test base provider."""
    with app.app_context():
        current_pidstore.register_minter("anothername", recid_minter)
