# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Extension tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from mock import patch

from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier


def test_version():
    """Test version import."""
    from invenio_pidstore import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioPIDStore(app)
    assert "invenio-pidstore" in app.extensions
    ext.register_minter(
        "testminter", lambda a, b: "deadbeef-c0de-c0de-c0de-b100dc0ffee5"
    )
    ext.register_fetcher(
        "testfetcher", lambda a, b: "deadbeef-c0de-c0de-c0de-b100dc0ffee5"
    )

    app = Flask("testapp")
    ext = InvenioPIDStore()
    assert "invenio-pidstore" not in app.extensions
    ext.init_app(app)
    assert "invenio-pidstore" in app.extensions


def test_logger():
    """Test extension initialization."""
    app = Flask("testapp")
    app.config["PIDSTORE_APP_LOGGER_HANDLERS"] = True
    InvenioPIDStore(app)


def test_invenio_records():
    """Test extension initialization."""
    app = Flask("testapp")
    with patch("invenio_pidstore.ext.importlib_metadata"):
        with patch("invenio_pidstore.ext.importlib_resources"):
            InvenioPIDStore(app)
    assert app.config["PIDSTORE_OBJECT_ENDPOINTS"]


def test_template_filters(app, db):
    """Test the template filters."""
    with app.app_context():
        # Test the 'pid_exists' template filter
        pid_exists = app.jinja_env.filters["pid_exists"]
        assert not pid_exists("pid_val0", pidtype="mock_t")
        PersistentIdentifier.create("mock_t", "pid_val0")
        db.session.commit()
        assert pid_exists("pid_val0", pidtype="mock_t")
        assert not pid_exists("foo", pidtype="mock_t")
        assert not pid_exists("pid_val0", pidtype="foo")
