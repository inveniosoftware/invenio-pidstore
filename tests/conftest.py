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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from click.testing import CliRunner
from flask import Flask
from flask_cli import FlaskCLI, ScriptInfo
from invenio_db import InvenioDB
from invenio_db.cli import db as db_cmd

from invenio_pidstore import InvenioPIDStore


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    # Set temporary instance path for sqlite
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)

    FlaskCLI(app)
    InvenioDB(app)
    InvenioPIDStore(app)

    app.config['PIDSTORE_PROVIDERS'] = app.config['PIDSTORE_PROVIDERS'] + \
        ['tests.mock_providers.mock_datacite:MockDataCite', ]

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
    )
    app.config.update(TESTING=True)

    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)

    runner.invoke(db_cmd, ['init'], obj=script_info)
    runner.invoke(db_cmd, ['create'], obj=script_info)

    def teardown():
        shutil.rmtree(instance_path)
        runner.invoke(db_cmd, ['destroy', '--yes-i-know'], obj=script_info)

    request.addfinalizer(teardown)

    return app
