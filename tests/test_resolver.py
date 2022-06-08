# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Resolver tests."""

from __future__ import absolute_import, print_function

import uuid

import pytest

from invenio_pidstore.errors import (
    PIDDeletedError,
    PIDDoesNotExistError,
    PIDMissingObjectError,
    PIDRedirectedError,
    PIDUnregistered,
)
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver


def test_resolver(app, db):
    """Test the class methods of PersistentIdentifier class."""
    status = [
        PIDStatus.NEW,
        PIDStatus.RESERVED,
        PIDStatus.REGISTERED,
        PIDStatus.DELETED,
    ]

    with app.app_context():
        i = 1
        rec_a = uuid.uuid4()

        # Create pids for each status with and without object
        for s in status:
            PersistentIdentifier.create("recid", i, status=s)
            i += 1
            if s != PIDStatus.DELETED:
                PersistentIdentifier.create(
                    "recid", i, status=s, object_type="rec", object_uuid=rec_a
                )
                i += 1

        # Create a DOI
        pid_doi = PersistentIdentifier.create(
            "doi",
            "10.1234/foo",
            status=PIDStatus.REGISTERED,
            object_type="rec",
            object_uuid=rec_a,
        )

        # Create redirects
        pid = PersistentIdentifier.create("recid", i, status=PIDStatus.REGISTERED)
        i += 1
        pid.redirect(PersistentIdentifier.get("recid", "2"))
        pid = PersistentIdentifier.create("recid", i, status=PIDStatus.REGISTERED)
        pid.redirect(pid_doi)
        db.session.commit()

        # Start tests
        resolver = Resolver(pid_type="recid", object_type="rec", getter=lambda x: x)

        # Resolve non-existing pid
        pytest.raises(PIDDoesNotExistError, resolver.resolve, "100")
        pytest.raises(PIDDoesNotExistError, resolver.resolve, "10.1234/foo")

        # Resolve status new
        pytest.raises(PIDUnregistered, resolver.resolve, "1")
        pytest.raises(PIDUnregistered, resolver.resolve, "2")

        # Resolve status reserved
        pytest.raises(PIDUnregistered, resolver.resolve, "3")
        pytest.raises(PIDUnregistered, resolver.resolve, "4")

        # Resolve status registered
        pytest.raises(PIDMissingObjectError, resolver.resolve, "5")
        pid, obj = resolver.resolve("6")
        assert pid and obj == rec_a

        # Resolve status deleted
        pytest.raises(PIDDeletedError, resolver.resolve, "7")

        # Resolve status redirected
        try:
            resolver.resolve("8")
            assert False
        except PIDRedirectedError as e:
            assert e.destination_pid.pid_type == "recid"
            assert e.destination_pid.pid_value == "2"

        try:
            resolver.resolve("9")
            assert False
        except PIDRedirectedError as e:
            assert e.destination_pid.pid_type == "doi"
            assert e.destination_pid.pid_value == "10.1234/foo"

        doiresolver = Resolver(pid_type="doi", object_type="rec", getter=lambda x: x)
        pytest.raises(PIDDoesNotExistError, doiresolver.resolve, "1")
        pid, obj = doiresolver.resolve("10.1234/foo")
        assert pid and obj == rec_a


def test_resolver_deleted_object(app, db):
    """Test the class methods of PersistentIdentifier class."""
    with app.app_context():
        rec_uuid = uuid.uuid4()
        records = {
            rec_uuid: {"title": "test"},
        }
        with db.session.begin_nested():
            pid = PersistentIdentifier.create(
                "recid",
                "1",
                status=PIDStatus.REGISTERED,
                object_type="rec",
                object_uuid=rec_uuid,
            )

        with db.session.begin_nested():
            pid.delete()

        resolver = Resolver(pid_type="recid", object_type="rec", getter=records.get)

        assert pytest.raises(PIDDeletedError, resolver.resolve, "1")


def test_resolver_not_registered_only(app, db):
    """Test the resolver returns a new and reserved PID when specified."""

    status = [PIDStatus.NEW, PIDStatus.RESERVED, PIDStatus.REGISTERED]

    with app.app_context():
        rec_a = uuid.uuid4()
        # Create pids for each status with and without object
        for idx, s in enumerate(status, 1):
            PersistentIdentifier.create("recid", idx * 2 - 1, status=s)
            PersistentIdentifier.create(
                "recid", idx * 2, status=s, object_type="rec", object_uuid=rec_a
            )

        db.session.commit()

        # Start tests
        resolver = Resolver(
            pid_type="recid",
            object_type="rec",
            getter=lambda x: x,
            registered_only=False,
        )

        # Resolve status new
        pytest.raises(PIDMissingObjectError, resolver.resolve, "1")
        pid, obj = resolver.resolve("2")
        assert pid and obj == rec_a

        # Resolve status reserved
        pytest.raises(PIDMissingObjectError, resolver.resolve, "3")
        pid, obj = resolver.resolve("4")
        assert pid and obj == rec_a

        # Resolve status registered
        pytest.raises(PIDMissingObjectError, resolver.resolve, "5")
        pid, obj = resolver.resolve("6")
        assert pid and obj == rec_a
