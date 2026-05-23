# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Define PIDStore proxies."""

from __future__ import absolute_import

from flask import current_app
from werkzeug.local import LocalProxy

current_pidstore = LocalProxy(lambda: current_app.extensions["invenio-pidstore"])
