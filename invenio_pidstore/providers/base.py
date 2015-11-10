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

"""Module storing implementations of PID providers."""

from __future__ import absolute_import, print_function

from ..models import PersistentIdentifier, PIDStatus


class BaseProvider(object):
    """Abstract class for persistent identifier provider classes."""

    pid_type = None
    """Default persistent identifier type."""

    pid_provider = None
    """Persistent identifier provider name."""

    default_status = PIDStatus.NEW
    """Default status for newly created PIDs by this provider."""

    @classmethod
    def create(cls, pid_type=None, pid_value=None, object_type=None,
               object_uuid=None, status=None, **kwargs):
        """Create a new instance for the given type and pid."""
        assert pid_value
        assert pid_type or cls.pid_type

        pid = PersistentIdentifier.create(
            pid_type or cls.pid_type,
            pid_value,
            pid_provider=cls.pid_provider,
            object_type=object_type,
            object_uuid=object_uuid,
            status=status or cls.default_status,
        )
        return cls(pid, **kwargs)

    @classmethod
    def get(cls, pid_value, pid_type=None, **kwargs):
        """Get a persistent identifier for this provider."""
        return cls(
            PersistentIdentifier.get(pid_type or cls.pid_type, pid_value,
                                     pid_provider=cls.pid_provider),
            **kwargs)

    def __init__(self, pid):
        """Initialize provider using persistent identifier."""
        self.pid = pid
        assert pid.pid_provider == self.pid_provider

    def reserve(self):
        """Reserve a the persistent identifier.

        This might or might not be useful depending on the service of the
        provider.
        """
        return self.pid.reserve()

    def register(self):
        """Register a the persistent identifier."""
        return self.pid.register()

    def update(self):
        """Update information about the persistent identifier."""

    def delete(self):
        """Delete a persistent identifier."""
        return self.pid.delete()

    def sync_status(self):
        """Synchronize PIDstatus with remote service provider."""
