# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Define PIDStore proxies."""

from __future__ import absolute_import

from flask import current_app
from werkzeug.local import LocalProxy

current_pidstore = LocalProxy(lambda: current_app.extensions["invenio-pidstore"])
