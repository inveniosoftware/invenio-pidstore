# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Fetcher tests."""

from __future__ import absolute_import, print_function

import uuid

from invenio_pidstore import current_pidstore
from invenio_pidstore.fetchers import recid_fetcher
from invenio_pidstore.minters import recid_minter


def test_recid_fetcher(app, db):
    """Test base provider."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        data = {}
        minted_pid = recid_minter(rec_uuid, data)
        fetched_pid = recid_fetcher(rec_uuid, data)
        assert minted_pid.pid_value == fetched_pid.pid_value
        assert fetched_pid.pid_type == fetched_pid.provider.pid_type
        assert fetched_pid.pid_type == 'recid'


def test_register_fetcher(app):
    """Test base provider."""
    with app.app_context():
        current_pidstore.register_fetcher('anothername', recid_minter)
