# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal Flask application example for development.

SPHINX-START

First install Invenio-PIDStore, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run

Open the admin page:

.. code-block:: console

    $ open http://127.0.0.1:5000/admin/recordmetadata/

Login with:

    username: admin@inveniosoftware.org

    password: 123456

To reset the example application run:

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
    DB_VERSIONING_USER_MODEL=None,
    SECRET_KEY="test_key",
    SECURITY_PASSWORD_HASH="pbkdf2_sha512",
    SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
    SECURITY_PASSWORD_SCHEMES=[
        "pbkdf2_sha512",
        "sha512_crypt",
        "invenio_aes_encrypted_email",
    ],
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
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
