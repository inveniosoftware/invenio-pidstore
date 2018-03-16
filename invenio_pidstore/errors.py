# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors for persistent identifiers."""

from __future__ import absolute_import, print_function


class PersistentIdentifierError(Exception):
    """Base class for PIDStore errors."""


class PIDValueError(PersistentIdentifierError):
    """Base class for value errors."""

    def __init__(self, pid_type, pid_value, *args, **kwargs):
        """Initialize exception."""
        self.pid_type = pid_type
        self.pid_value = pid_value
        super(PIDValueError, self).__init__(*args, **kwargs)


class PIDDoesNotExistError(PIDValueError):
    """PID does not exists error."""


class PIDAlreadyExists(PIDValueError):
    """Persistent identifier already exists error."""


class ResolverError(PersistentIdentifierError):
    """Persistent identifier does not exists."""

    def __init__(self, pid, *args, **kwargs):
        """Initialize exception."""
        self.pid = pid
        super(ResolverError, self).__init__(*args, **kwargs)


class PIDDeletedError(ResolverError):
    """Persistent identifier is deleted."""

    def __init__(self, pid, record, *args, **kwargs):
        """Initialize exception."""
        self.record = record
        super(PIDDeletedError, self).__init__(pid, *args, **kwargs)


class PIDMissingObjectError(ResolverError):
    """Persistent identifier has no object."""


class PIDUnregistered(ResolverError):
    """Persistent identifier has not been registered."""


class PIDRedirectedError(ResolverError):
    """Persistent identifier is redirected to another pid."""

    def __init__(self, pid, dest_pid, *args, **kwargs):
        """Initialize exception."""
        self.destination_pid = dest_pid
        super(PIDRedirectedError, self).__init__(pid, *args, **kwargs)


class PIDObjectAlreadyAssigned(PersistentIdentifierError):
    """Persistent identifier is already assigned to another object."""


class PIDInvalidAction(PersistentIdentifierError):
    """Invalid operation on persistent identifier in current state."""
