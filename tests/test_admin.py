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
"""Admin interface tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from flask_admin import Admin, menu
from flask_cli import FlaskCLI
from invenio_db import InvenioDB, db

from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.admin import pid_adminview


def test_admin():
    """Test flask-admin interace."""
    app = Flask('testapp')
    FlaskCLI(app)
    InvenioDB(app)
    InvenioPIDStore(app)
    admin = Admin(app, name="AdminExt")

    pid_kwargs = dict(pid_adminview)

    assert 'model' in pid_adminview
    assert 'modelview' in pid_adminview

    # Register both models in admin
    pid_model = pid_kwargs.pop('model')
    pid_mv = pid_kwargs.pop('modelview')
    admin.add_view(pid_mv(pid_model, db.session, **pid_kwargs))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}

    # PIDStore should be a category
    assert 'Records' in menu_items
    assert menu_items['Records'].is_category()
    assert isinstance(menu_items['Records'], menu.MenuCategory)

    # Items in PIDStore menu should be the modelviews
    submenu_items = {str(item.name): item for item in
                     menu_items['Records'].get_children()}
    assert 'Persistent Identifier' in submenu_items
    assert isinstance(submenu_items['Persistent Identifier'], menu.MenuView)
