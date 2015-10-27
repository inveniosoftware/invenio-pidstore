# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Mock of the DataCite PID provider."""

from __future__ import absolute_import

from invenio_pidstore.provider import PidProvider


class MockDataCite(PidProvider):
    """This is a Mock of a DOI provider, using DataCite API."""

    pid_type = 'mock_t'

    def __init__(self):
        """Initialize provider."""

    def _get_url(self, kwargs):
        try:
            return kwargs['url']
        except KeyError:
            raise Exception("url keyword argument must be specified.")

    def _get_doc(self, kwargs):
        try:
            return kwargs['doc']
        except KeyError:
            raise Exception("doc keyword argument must be specified.")

    def reserve(self, pid, *args, **kwargs):
        """Reserve a new persistent identifier.

        This might or might not be useful depending on the service of the
        provider.
        """
        return True

    def register(self, pid, *args, **kwargs):
        """Register a new persistent identifier."""
        return True

    def update(self, pid, *args, **kwargs):
        """Update information about a persistent identifier."""
        return True

    def delete(self, pid, *args, **kwargs):
        """Delete a persistent identifier."""
        return True

    def sync_status(self, pid, *args, **kwargs):
        """Synchronize DOI status DataCite MDS."""
        return True

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        """Return provider for a given pid."""
        return True


class MissingPidType(PidProvider):
    """
    This is an invalid PidProvider definition.

    This class is used for testing.
    Each custom PID provider must define a class variable 'pid_type'.
    """


class PidProviderNotInheriting(object):
    """
    This is an invalid PidProvider definition.

    This class is used for testing.
    Each custom PID provider must inherit after PidProvider class.
    """

    pid_type = 'mytype'
