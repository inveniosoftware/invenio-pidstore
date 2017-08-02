# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
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


"""Minimal Flask application example for development.

SPHINX-START

Start the Redis server.

Install the requirements:

.. code-block:: console

    $ pip install -e .[all]
    $ cd examples
    $ ./app-setup.sh
    $ ./app-fixtures.sh

Run example development server:

.. code-block:: console

    $ FLASK_APP=app.py flask run --debugger -p 5000

Open the admin page:

.. code-block:: console

    $ open http://0.0.0.0:5000/admin/recordmetadata/

Make a login with:

    username: admin@inveniosoftware.org

    password: 123456

At the end, don't forget to clean-up your folder:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END

"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB
from invenio_records import InvenioRecords

from invenio_pidstore import InvenioPIDStore

# Create Flask application
app = Flask(__name__)
app.config.update(
    SECRET_KEY='test_key',
    SECURITY_PASSWORD_HASH='pbkdf2_sha512',
    SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
    SECURITY_PASSWORD_SCHEMES=[
        'pbkdf2_sha512', 'sha512_crypt', 'invenio_aes_encrypted_email'
    ],
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
    ),
    WTF_CSRF_ENABLED=False,
)

Babel(app)
Menu(app)
InvenioDB(app)
admin = InvenioAdmin(app)
InvenioPIDStore(app)
accounts = InvenioAccounts(app)
InvenioAccess(app)
InvenioRecords(app)

# register blueprints
app.register_blueprint(accounts_blueprint)
