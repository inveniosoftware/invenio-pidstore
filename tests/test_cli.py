# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""CLI tests."""

from __future__ import absolute_import, print_function

import uuid

from click.testing import CliRunner
from flask.cli import ScriptInfo

from invenio_pidstore.cli import pid as cmd
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


def test_pid_creation(app, db):
    """Test pid creation."""
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda: app)

    with runner.isolated_filesystem():
        with app.app_context():
            assert PersistentIdentifier.query.count() == 0

        result = runner.invoke(cmd, ["create", "doi", "10.1234/foo"], obj=script_info)
        assert 0 == result.exit_code

        with app.app_context():
            assert PersistentIdentifier.query.count() == 1
            pid = PersistentIdentifier.get("doi", "10.1234/foo")
            assert pid.pid_type == "doi"
            assert pid.pid_value == "10.1234/foo"
            assert pid.pid_provider is None
            assert pid.status == PIDStatus.NEW
            assert pid.object_type is None
            assert pid.object_uuid is None

        rec_uuid = uuid.uuid4()

        # Bad parameter status:
        result = runner.invoke(
            cmd,
            [
                "create",
                "recid",
                "2",
                "--status",
                "BADPARAMETER",
                "--type",
                "rec",
                "--uuid",
                str(rec_uuid),
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        # Any or both type and uuid must be defined:
        result = runner.invoke(
            cmd,
            [
                "create",
                "recid",
                "2",
                "--type",
                "rec",
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        result = runner.invoke(
            cmd,
            [
                "create",
                "recid",
                "2",
                "--uuid",
                str(rec_uuid),
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        # Everything should be fine now:
        result = runner.invoke(
            cmd,
            [
                "create",
                "recid",
                "2",
                "--status",
                "REGISTERED",
                "--type",
                "rec",
                "--uuid",
                str(rec_uuid),
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code

        with app.app_context():
            assert PersistentIdentifier.query.count() == 2
            pid = PersistentIdentifier.get("recid", "2")
            assert pid.pid_type == "recid"
            assert pid.pid_value == "2"
            assert pid.pid_provider is None
            assert pid.status == PIDStatus.REGISTERED
            assert pid.object_type == "rec"
            assert pid.object_uuid == rec_uuid

        # Can't duplicate existing persistent identifier
        result = runner.invoke(
            cmd,
            [
                "create",
                "recid",
                "2",
            ],
            obj=script_info,
        )
        assert 1 == result.exit_code


def test_pid_assign(app, db):
    """Test pid object assignment."""
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda: app)

    with runner.isolated_filesystem():
        # No assigned object
        result = runner.invoke(cmd, ["create", "doi", "10.1234/foo"], obj=script_info)
        assert 0 == result.exit_code

        with app.app_context():
            pid = PersistentIdentifier.get("doi", "10.1234/foo")
            assert not pid.has_object()
            assert pid.get_assigned_object() is None
            assert pid.get_assigned_object("rec") is None

        # Assign object
        rec_uuid = uuid.uuid4()
        result = runner.invoke(
            cmd,
            ["assign", "doi", "10.1234/foo", "-t", "rec", "-i", str(rec_uuid)],
            obj=script_info,
        )
        assert 0 == result.exit_code
        with app.app_context():
            pid = PersistentIdentifier.get("doi", "10.1234/foo")
            assert pid.has_object()
            assert pid.get_assigned_object() == rec_uuid
            assert pid.get_assigned_object("rec") == rec_uuid
            assert pid.get_assigned_object("oth") is None

        # Doesnt' raise
        result = runner.invoke(
            cmd,
            ["assign", "doi", "10.1234/foo", "-t", "rec", "-i", str(rec_uuid)],
            obj=script_info,
        )
        assert 0 == result.exit_code

        # Missing type or uuid:
        result = runner.invoke(
            cmd,
            [
                "assign",
                "doi",
                "10.1234/foo",
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        result = runner.invoke(
            cmd,
            [
                "assign",
                "doi",
                "10.1234/foo",
                "-t",
                "rec",
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        result = runner.invoke(
            cmd,
            [
                "assign",
                "doi",
                "10.1234/foo",
                "-i",
                str(rec_uuid),
            ],
            obj=script_info,
        )
        assert 2 == result.exit_code

        # Assign without overwrite (uuid as str and uuid)
        new_uuid = uuid.uuid4()
        result = runner.invoke(
            cmd,
            ["assign", "doi", "10.1234/foo", "-t", "rec", "-i", str(new_uuid)],
            obj=script_info,
        )

        assert 1 == result.exit_code

        # Assign with overwrite
        result = runner.invoke(
            cmd,
            [
                "assign",
                "doi",
                "10.1234/foo",
                "-s",
                "REGISTERED",
                "-t",
                "rec",
                "-i",
                str(new_uuid),
                "--overwrite",
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code

        with app.app_context():
            pid = PersistentIdentifier.get("doi", "10.1234/foo")
            assert pid.has_object()
            assert pid.status == PIDStatus.REGISTERED
            assert pid.get_assigned_object() == new_uuid
            assert pid.get_assigned_object("rec") == new_uuid
            assert pid.get_assigned_object("oth") is None


def test_pid_unassign(app, db):
    """Test pid object unassignment."""
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda: app)

    with runner.isolated_filesystem():
        rec_uuid = uuid.uuid4()
        # Assigned object
        result = runner.invoke(
            cmd,
            ["create", "recid", "101", "-t", "rec", "-i", str(rec_uuid)],
            obj=script_info,
        )
        assert 0 == result.exit_code

        result = runner.invoke(
            cmd,
            [
                "get",
                "recid",
                "101",
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code
        assert "rec {0} N\n".format(str(rec_uuid)) == result.output

        result = runner.invoke(
            cmd,
            [
                "dereference",
                "rec",
                str(rec_uuid),
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code
        assert "recid 101 None\n" == result.output

        result = runner.invoke(
            cmd,
            [
                "dereference",
                "rec",
                str(rec_uuid),
                "-s",
                "NEW",
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code
        assert "recid 101 None\n" == result.output

        with app.app_context():
            pid = PersistentIdentifier.get("recid", "101")
            assert pid.has_object()
            assert pid.get_assigned_object() == rec_uuid
            assert pid.get_assigned_object("rec") == rec_uuid

        # Unassign the object
        result = runner.invoke(
            cmd,
            [
                "unassign",
                "recid",
                "101",
            ],
            obj=script_info,
        )
        assert 0 == result.exit_code

        with app.app_context():
            pid = PersistentIdentifier.get("recid", "101")
            assert not pid.has_object()
            assert pid.get_assigned_object() is None
            assert pid.get_assigned_object("rec") is None
