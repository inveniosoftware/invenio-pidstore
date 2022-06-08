# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that stores and registers persistent identifiers."""

from __future__ import absolute_import, print_function

import importlib_metadata
import importlib_resources

from . import config
from .cli import pid as cmd
from .errors import PIDDoesNotExistError
from .models import PersistentIdentifier, logger


def pid_exists(value, pidtype=None):
    """Check if a persistent identifier exists.

    :param value: The PID value.
    :param pidtype: The pid value (Default: None).
    :returns: `True` if the PID exists.
    """
    try:
        PersistentIdentifier.get(pidtype, value)
        return True
    except PIDDoesNotExistError:
        return False


class _PIDStoreState(object):
    """Persistent identifier store state."""

    def __init__(
        self, app, minters_entry_point_group=None, fetchers_entry_point_group=None
    ):
        """Initialize state."""
        self.app = app
        self.minters = {}
        self.fetchers = {}
        if minters_entry_point_group:
            self.load_minters_entry_point_group(minters_entry_point_group)
        if fetchers_entry_point_group:
            self.load_fetchers_entry_point_group(fetchers_entry_point_group)

    def register_minter(self, name, minter):
        """Register a minter.

        :param name: Minter name.
        :param minter: The new minter.
        """
        if name not in self.minters:
            self.minters[name] = minter

    def register_fetcher(self, name, fetcher):
        """Register a fetcher.

        :param name: Fetcher name.
        :param fetcher: The new fetcher.
        """
        if name not in self.fetchers:
            self.fetchers[name] = fetcher

    def load_minters_entry_point_group(self, entry_point_group):
        """Load minters from an entry point group.

        :param entry_point_group: The entrypoint group.
        """
        for ep in importlib_metadata.entry_points(group=entry_point_group):
            self.register_minter(ep.name, ep.load())

    def load_fetchers_entry_point_group(self, entry_point_group):
        """Load fetchers from an entry point group.

        :param entry_point_group: The entrypoint group.
        """
        for ep in importlib_metadata.entry_points(group=entry_point_group):
            self.register_fetcher(ep.name, ep.load())


class InvenioPIDStore(object):
    """Invenio-PIDStore extension."""

    def __init__(
        self,
        app=None,
        minters_entry_point_group="invenio_pidstore.minters",
        fetchers_entry_point_group="invenio_pidstore.fetchers",
    ):
        """Extension initialization.

        :param minters_entry_point_group: The entrypoint for minters.
            (Default: `invenio_pidstore.minters`).
        :param fetchers_entry_point_group: The entrypoint for fetchers.
            (Default: `invenio_pidstore.fetchers`).
        """
        if app:
            self._state = self.init_app(
                app,
                minters_entry_point_group=minters_entry_point_group,
                fetchers_entry_point_group=fetchers_entry_point_group,
            )

    def init_app(
        self, app, minters_entry_point_group=None, fetchers_entry_point_group=None
    ):
        """Flask application initialization.

        Initialize:

        * The CLI commands.

        * Initialize the logger (Default: `app.debug`).

        * Initialize the default admin object link endpoint.
            (Default: `{"rec": "recordmetadata.details_view"}` if
            `invenio-records` is installed, otherwise `{}`).

        * Register the `pid_exists` template filter.

        * Initialize extension state.

        :param app: The Flask application
        :param minters_entry_point_group: The minters entry point group
            (Default: None).
        :param fetchers_entry_point_group: The fetchers entry point group
            (Default: None).
        :returns: PIDStore state application.
        """
        self.init_config(app)
        # Initialize CLI
        app.cli.add_command(cmd)

        # Initialize logger
        app.config.setdefault("PIDSTORE_APP_LOGGER_HANDLERS", app.debug)
        if app.config["PIDSTORE_APP_LOGGER_HANDLERS"]:
            for handler in app.logger.handlers:
                logger.addHandler(handler)

        # Initialize admin object link endpoints.
        try:
            importlib_metadata.version("invenio-records")
            app.config.setdefault(
                "PIDSTORE_OBJECT_ENDPOINTS",
                dict(
                    rec="recordmetadata.details_view",
                ),
            )
        except importlib_metadata.PackageNotFoundError:
            app.config.setdefault("PIDSTORE_OBJECT_ENDPOINTS", {})

        # Register template filter
        app.jinja_env.filters["pid_exists"] = pid_exists

        # Initialize extension state.
        state = _PIDStoreState(
            app=app,
            minters_entry_point_group=minters_entry_point_group,
            fetchers_entry_point_group=fetchers_entry_point_group,
        )
        app.extensions["invenio-pidstore"] = state
        return state

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("PIDSTORE_") and k not in (
                "PIDSTORE_OBJECT_ENDPOINTS",
                "PIDSTORE_APP_LOGGER_HANDLERS",
            ):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)
