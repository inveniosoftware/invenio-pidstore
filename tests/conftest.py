# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from invenio_db import InvenioDB
from invenio_i18n import InvenioI18N
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_pidstore import InvenioPIDStore


@pytest.yield_fixture()
def app(request):
    """Flask application fixture."""
    # Set temporary instance path for sqlite
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp", instance_path=instance_path)
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

    # Teardown instance path.
    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    from invenio_db import db as db_

    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()
