# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""DataCite PID provider."""

from __future__ import absolute_import

import copy

from base32_lib import base32
from flask import current_app

from ..models import PIDStatus
from .base import BaseProvider


class RecordIdProviderV2(BaseProvider):
    """Record identifier provider V2.

    This is the recommended record id provider.

    It generates a random alphanumeric string as opposed to an increasing
    integer (:class:`invenio_pidstore.providers.recordid.RecordIdProvider`).
    """

    pid_type = "recid"
    """Type of persistent identifier."""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of record ids.
    """

    default_status_with_obj = PIDStatus.REGISTERED
    """Record IDs are by default registered immediately.

    Default: :attr:`invenio_pidstore.models.PIDStatus.REGISTERED`
    """

    default_status = PIDStatus.RESERVED
    """Record IDs with an object are by default reserved.

    Default: :attr:`invenio_pidstore.models.PIDStatus.RESERVED`
    """

    @classmethod
    def generate_id(cls, options=None):
        """Generate record id."""
        passed_options = options or {}
        # WHY: A new dict needs to be created to prevent side-effects
        options = copy.deepcopy(current_app.config.get("PIDSTORE_RECORDID_OPTIONS", {}))
        options.update(passed_options)
        length = options.get("length", 10)
        split_every = options.get("split_every", 0)
        checksum = options.get("checksum", True)

        return base32.generate(
            length=length, split_every=split_every, checksum=checksum
        )

    @classmethod
    def create(cls, object_type=None, object_uuid=None, options=None, **kwargs):
        """Create a new record identifier.

        Note: if the object_type and object_uuid values are passed, then the
        PID status will be automatically setted to
        :attr:`invenio_pidstore.models.PIDStatus.REGISTERED`.

        For more information about parameters,
        see :meth:`invenio_pidstore.providers.base.BaseProvider.create`.

        :param object_type: The object type. (Default: None.)
        :param object_uuid: The object identifier. (Default: None).
        :param options: ``dict`` with optional keys:
            ``"length"`` (integer), ``"split_every"`` (integer),
            ``"checksum"`` (boolean). (Default: None).
        :param kwargs: dict to hold generated pid_value and status. See
            :meth:`invenio_pidstore.providers.base.BaseProvider.create` extra
            parameters.
        :returns: A :class:`RecordIdProviderV2` instance.
        """
        assert "pid_value" not in kwargs

        kwargs["pid_value"] = cls.generate_id(options)
        kwargs.setdefault("status", cls.default_status)

        if object_type and object_uuid:
            kwargs["status"] = cls.default_status_with_obj

        return super(RecordIdProviderV2, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs
        )
