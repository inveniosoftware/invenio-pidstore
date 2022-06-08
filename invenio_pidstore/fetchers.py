# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier fetchers.

A proper fetcher is defined as a function that return a
:data:`invenio_pidstore.fetchers.FetchedPID` instance.

E.g.

.. code-block:: python

    def my_fetcher(record_uuid, data):
        return FetchedPID(
            provider=MyRecordIdProvider,
            pid_type=MyRecordIdProvider.pid_type,
            pid_value=extract_pid_value(data),
        )

To see more about providers see :mod:`invenio_pidstore.providers`.
"""

from __future__ import absolute_import, print_function

from collections import namedtuple

from flask import current_app

from .providers.recordid import RecordIdProvider
from .providers.recordid_v2 import RecordIdProviderV2

FetchedPID = namedtuple("FetchedPID", ["provider", "pid_type", "pid_value"])
"""A pid fetcher."""


def recid_fetcher_v2(record_uuid, data):
    """Fetch a record's identifiers.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :returns: A :data:`invenio_pidstore.fetchers.FetchedPID` instance.
    """
    pid_field = current_app.config["PIDSTORE_RECID_FIELD"]
    return FetchedPID(
        provider=RecordIdProviderV2,
        pid_type=RecordIdProviderV2.pid_type,
        pid_value=str(data[pid_field]),
    )


def recid_fetcher(record_uuid, data):
    """Legacy way to fetch a record's identifiers.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :returns: A :data:`invenio_pidstore.fetchers.FetchedPID` instance.
    """
    pid_field = current_app.config["PIDSTORE_RECID_FIELD"]
    return FetchedPID(
        provider=RecordIdProvider,
        pid_type=RecordIdProvider.pid_type,
        pid_value=str(data[pid_field]),
    )
