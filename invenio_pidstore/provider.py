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

"""Define APIs for PID providers."""

from __future__ import absolute_import, print_function

from .registry import pidproviders


class PIDStatus:
    """Constants for possible status of any given PID."""

    NEW = 'N'
    """
    The pid has *not* yet been registered with the service provider.
    """

    REGISTERED = 'R'
    """
    The pid has been registered with the service provider.
    """

    DELETED = 'D'
    """
    The pid has been deleted/inactivated with the service proivider.
    This should very rarely happen, and must be kept track of, as the PID
    should not be reused for something else.
    """

    RESERVED = 'K'
    """
    The pid has been reserved in the service provider but not yet fully
    registered.
    """


class PidProvider(object):
    """Abstract class for persistent identifier provider classes.

    Subclasses must implement register, update, delete and is_provider_for_pid
    methods as well be added to the app.config['PIDSTORE_PROVIDERS']
    or manually added to the registry dict (see static field 'registry' below).

    The provider is responsible for handling of errors, as well as logging of
    actions happening to the pid (see invenio_pidstore.providers.DataCite).

    Each method takes variable number of argument and keywords arguments. This
    can be used to pass additional information to the provider when registering
    a persistent identifier. E.g. a DOI requires URL and metadata to be able to
    register the DOI.
    """

    pid_type = None
    """
    Must be overwritten in subcleass and specified as a string (max len 6)
    """

    @staticmethod
    def create(pid_type, pid_str, pid_provider, *args, **kwargs):
        """Create a new instance for the given type and pid."""
        providers = pidproviders.get(pid_type.lower(), [])
        for p in providers:
            if p.is_provider_for_pid(pid_str):
                return p(*args, **kwargs)
        return None

    #
    # API methods which must be implemented by each provider.
    #
    def reserve(self, pid, *args, **kwargs):
        """Reserve a new persistent identifier.

        This might or might not be useful depending on the service of the
        provider.
        """
        raise NotImplementedError  # pragma: no cover

    def register(self, pid, *args, **kwargs):
        """Register a new persistent identifier."""
        raise NotImplementedError  # pragma: no cover

    def update(self, pid, *args, **kwargs):
        """Update information about a persistent identifier."""
        raise NotImplementedError  # pragma: no cover

    def delete(self, pid, *args, **kwargs):
        """Delete a persistent identifier."""
        raise NotImplementedError  # pragma: no cover

    def sync_status(self, pid, *args, **kwargs):
        """Synchronize PIDstatus with remote service provider."""
        return True

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        """Determine whether this class is the provider of given PID."""
        raise NotImplementedError  # pragma: no cover

    #
    # API methods which might need to be implemented depending on each
    # provider.
    #
    def create_new_pid(self, pid_value):
        """Some PidProvider might have the ability to create new values."""
        return pid_value


class LocalPidProvider(PidProvider):
    """Abstract class for local PIDs (i.e locally unmanaged DOIs)."""

    def reserve(self, pid, *args, **kwargs):
        """Reserve given pid."""
        pid.log("RESERVE", "Successfully reserved locally")
        return True

    def register(self, pid, *args, **kwargs):
        """Register given pid."""
        pid.log("REGISTER", "Successfully registered locally")
        return True

    def update(self, pid, *args, **kwargs):
        """Update given pid."""
        # No logging necessary as status of PID is not changing
        return True

    def delete(self, pid, *args, **kwargs):
        """Delete a registered DOI."""
        pid.log("DELETE", "Successfully deleted locally")
        return True
