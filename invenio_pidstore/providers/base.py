# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
    def create(
        cls,
        pid_type=None,
        pid_value=None,
        object_type=None,
        object_uuid=None,
        status=None,
        **kwargs
    ):
        """Create a new instance for the given type and pid.

        :param pid_type: Persistent identifier type. (Default: None).
        :param pid_value: Persistent identifier value. (Default: None).
        :param status: Current PID status.
            (Default: :attr:`invenio_pidstore.models.PIDStatus.NEW`)
        :param object_type: The object type is a string that identify its type.
            (Default: None).
        :param object_uuid: The object UUID. (Default: None).
        :returns: A :class:`invenio_pidstore.providers.base.BaseProvider`
            instance.
        """
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
        """Get a persistent identifier for this provider.

        :param pid_type: Persistent identifier type. (Default: configured
            :attr:`invenio_pidstore.providers.base.BaseProvider.pid_type`)
        :param pid_value: Persistent identifier value.
        :param kwargs: See
            :meth:`invenio_pidstore.providers.base.BaseProvider` required
            initialization properties.
        :returns: A :class:`invenio_pidstore.providers.base.BaseProvider`
            instance.
        """
        return cls(
            PersistentIdentifier.get(
                pid_type or cls.pid_type, pid_value, pid_provider=cls.pid_provider
            ),
            **kwargs
        )

    def __init__(self, pid, **kwargs):
        """Initialize provider using persistent identifier.

        :param pid: A :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        """
        self.pid = pid
        assert pid.pid_provider == self.pid_provider

    def reserve(self):
        """Reserve a persistent identifier.

        This might or might not be useful depending on the service of the
        provider.

        See: :meth:`invenio_pidstore.models.PersistentIdentifier.reserve`.
        """
        return self.pid.reserve()

    def register(self):
        """Register a persistent identifier.

        See: :meth:`invenio_pidstore.models.PersistentIdentifier.register`.
        """
        return self.pid.register()

    def update(self):
        """Update information about the persistent identifier."""
        pass

    def delete(self):
        """Delete a persistent identifier.

        See: :meth:`invenio_pidstore.models.PersistentIdentifier.delete`.
        """
        return self.pid.delete()

    def sync_status(self):
        """Synchronize PIDstatus with remote service provider."""
        pass
