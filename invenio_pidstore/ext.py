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

"""Invenio module that stores and registers persistent identifiers."""

from __future__ import absolute_import, print_function

import pkg_resources

from .cli import pid as cmd
from .errors import PIDDoesNotExistError
from .models import PersistentIdentifier, logger


def pid_exists(value, pidtype=None):
    """Check if a persistent identifier exists."""
    try:
        PersistentIdentifier.get(pidtype, value)
        return True
    except PIDDoesNotExistError:
        return False


class _PIDStoreState(object):
    """Persistent identifier store state."""

    def __init__(self, app, minters_entry_point_group=None,
                 fetchers_entry_point_group=None):
        """Initialize state."""
        self.app = app
        self.minters = {}
        self.fetchers = {}
        if minters_entry_point_group:
            self.load_minters_entry_point_group(minters_entry_point_group)
        if fetchers_entry_point_group:
            self.load_fetchers_entry_point_group(fetchers_entry_point_group)

    def register_minter(self, name, minter):
        """Register a minter."""
        assert name not in self.minters
        self.minters[name] = minter

    def register_fetcher(self, name, fetcher):
        """Register a fetcher."""
        assert name not in self.fetchers
        self.fetchers[name] = fetcher

    def load_minters_entry_point_group(self, entry_point_group):
        """Load minters from an entry point group."""
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_minter(ep.name, ep.load())

    def load_fetchers_entry_point_group(self, entry_point_group):
        """Load fetchers from an entry point group."""
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_fetcher(ep.name, ep.load())


class InvenioPIDStore(object):
    """Invenio-PIDStore extension."""

    def __init__(self, app=None,
                 minters_entry_point_group='invenio_pidstore.minters',
                 fetchers_entry_point_group='invenio_pidstore.fetchers'):
        """Extension initialization."""
        if app:
            self._state = self.init_app(
                app, minters_entry_point_group=minters_entry_point_group,
                fetchers_entry_point_group=fetchers_entry_point_group
            )

    def init_app(self, app, minters_entry_point_group=None,
                 fetchers_entry_point_group=None):
        """Flask application initialization."""
        # Initialize CLI
        app.cli.add_command(cmd)

        # Initialize logger
        app.config.setdefault('PIDSTORE_APP_LOGGER_HANDLERS', app.debug)
        if app.config['PIDSTORE_APP_LOGGER_HANDLERS']:
            for handler in app.logger.handlers:
                logger.addHandler(handler)

        # Initialize admin object link endpoints.
        try:
            pkg_resources.get_distribution('invenio-records')
            app.config.setdefault('PIDSTORE_OBJECT_ENDPOINTS', dict(
                rec='recordmetadata.details_view',
            ))
        except pkg_resources.DistributionNotFound:
            app.config.setdefault('PIDSTORE_OBJECT_ENDPOINTS', {})

        # Register template filter
        app.jinja_env.filters['pid_exists'] = pid_exists

        # Initialize extension state.
        state = _PIDStoreState(
            app=app,
            minters_entry_point_group=minters_entry_point_group,
            fetchers_entry_point_group=fetchers_entry_point_group,
        )
        app.extensions['invenio-pidstore'] = state
        return state

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)
