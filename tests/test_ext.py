# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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


"""Extension tests."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask import Flask
from invenio_db import db
from mock import patch

from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier


def test_version():
    """Test version import."""
    from invenio_pidstore import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    ext = InvenioPIDStore(app)
    assert 'invenio-pidstore' in app.extensions
    ext.register_minter('testminter',
                        lambda a, b: 'deadbeef-c0de-c0de-c0de-b100dc0ffee5')
    ext.register_fetcher('testfetcher',
                         lambda a, b: 'deadbeef-c0de-c0de-c0de-b100dc0ffee5')

    app = Flask('testapp')
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    ext = InvenioPIDStore()
    assert 'invenio-pidstore' not in app.extensions
    ext.init_app(app)
    assert 'invenio-pidstore' in app.extensions


def test_logger():
    """Test extension initialization."""
    app = Flask('testapp')
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    app.config['PIDSTORE_APP_LOGGER_HANDLERS'] = True
    InvenioPIDStore(app)


def test_no_invenio_records():
    """Test extension initialization."""
    app = Flask('testapp')
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    with patch('invenio_pidstore.ext.pkg_resources') as obj:
        obj.DistributionNotFound = pkg_resources.DistributionNotFound
        obj.get_distribution.side_effect = pkg_resources.DistributionNotFound
        InvenioPIDStore(app)
    assert app.config['PIDSTORE_OBJECT_ENDPOINTS'] == {}


def test_template_filters(app):
    """Test the template filters."""
    with app.app_context():
        # Test the 'pid_exists' template filter
        pid_exists = app.jinja_env.filters['pid_exists']
        assert not pid_exists('pid_val0', pidtype='mock_t')
        PersistentIdentifier.create('mock_t', 'pid_val0')
        db.session.commit()
        assert pid_exists('pid_val0', pidtype='mock_t')
        assert not pid_exists('foo', pidtype='mock_t')
        assert not pid_exists('pid_val0', pidtype='foo')
