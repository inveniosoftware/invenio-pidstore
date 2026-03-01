# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os

import pytest
from flask import Flask
from invenio_app.factory import create_app as _create_app
from invenio_db import InvenioDB
from invenio_i18n import InvenioI18N

from invenio_pidstore import InvenioPIDStore


@pytest.fixture
def app_admin(request):
    """Flask application fixture."""
    app = Flask("testapp")
    InvenioDB(app)
    InvenioI18N(app)
    InvenioPIDStore(app)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        TESTING=True,
    )

    with app.app_context():
        yield app


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture for use with pytest-invenio."""
    return _create_app
