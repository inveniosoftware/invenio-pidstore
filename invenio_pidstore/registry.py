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

"""Registry for PidProviders."""

from __future__ import absolute_import, print_function

from flask import _app_ctx_stack, current_app
from werkzeug.local import LocalProxy
from werkzeug.utils import import_string

__all__ = ("pidproviders", )


def _collect_pidproviders():
    """Register the providers from the configuration."""
    from .provider import PidProvider
    registry_dict = dict()
    for provider_str in current_app.config['PIDSTORE_PROVIDERS']:
        provider = import_string(provider_str)
        if not issubclass(provider, PidProvider):
            raise TypeError("Argument not an instance of PidProvider.")
        pid_type = getattr(provider, 'pid_type', None)
        if pid_type is None:
            raise AttributeError(
                "Provider must specify class variable pid_type."
            )
        pid_type = pid_type.lower()
        if pid_type not in registry_dict:
            registry_dict[pid_type] = []

        # Prevent double registration
        if provider not in registry_dict[pid_type]:
            registry_dict[pid_type].append(provider)
    return registry_dict


def _pidproviders():
    """Proxy for the registry to preserve it on the application context."""
    if not hasattr(_app_ctx_stack, '_invenio_pidprovider_registry'):
        _app_ctx_stack._invenio_pidprovider_registry = _collect_pidproviders()
    return _app_ctx_stack._invenio_pidprovider_registry


pidproviders = LocalProxy(_pidproviders)
"""Registry of possible providers."""
