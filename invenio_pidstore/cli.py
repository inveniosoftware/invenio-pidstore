# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for PIDStore management."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext
from invenio_db import db

from .proxies import current_pidstore


def process_status(ctx, param, value):
    """Return status value."""
    from .models import PIDStatus

    # Allow empty status
    if value is None:
        return None

    if not hasattr(PIDStatus, value):
        raise click.BadParameter(
            "Status needs to be one of {0}.".format(
                ", ".join([s.name for s in PIDStatus])
            )
        )
    return getattr(PIDStatus, value)


#
# PIDStore management commands
#


@click.group()
def pid():
    """PID-Store management commands."""


@pid.command()
@click.argument("pid_type")
@click.argument("pid_value")
@click.option("-s", "--status", default="NEW", callback=process_status)
@click.option("-t", "--type", "object_type", default=None)
@click.option("-i", "--uuid", "object_uuid", default=None)
@with_appcontext
def create(pid_type, pid_value, status, object_type, object_uuid):
    """Create new persistent identifier."""
    from .models import PersistentIdentifier

    if bool(object_type) ^ bool(object_uuid):
        raise click.BadParameter("Speficy both or any of --type and --uuid.")

    new_pid = PersistentIdentifier.create(
        pid_type,
        pid_value,
        status=status,
        object_type=object_type,
        object_uuid=object_uuid,
    )
    db.session.commit()
    click.echo("{0.pid_type} {0.pid_value} {0.pid_provider}".format(new_pid))


@pid.command()
@click.argument("pid_type")
@click.argument("pid_value")
@click.option("-s", "--status", default=None, callback=process_status)
@click.option("-t", "--type", "object_type", required=True)
@click.option("-i", "--uuid", "object_uuid", required=True)
@click.option("--overwrite", is_flag=True, default=False)
@with_appcontext
def assign(pid_type, pid_value, status, object_type, object_uuid, overwrite):
    """Assign persistent identifier."""
    from .models import PersistentIdentifier

    obj = PersistentIdentifier.get(pid_type, pid_value)
    if status is not None:
        obj.status = status
    obj.assign(object_type, object_uuid, overwrite=overwrite)
    db.session.commit()
    click.echo(obj.status)


@pid.command()
@click.argument("pid_type")
@click.argument("pid_value")
@with_appcontext
def unassign(pid_type, pid_value):
    """Unassign persistent identifier."""
    from .models import PersistentIdentifier

    obj = PersistentIdentifier.get(pid_type, pid_value)
    obj.unassign()
    db.session.commit()
    click.echo(obj.status)


@pid.command("get")
@click.argument("pid_type")
@click.argument("pid_value")
@with_appcontext
def get_object(pid_type, pid_value):
    """Get an object behind persistent identifier."""
    from .models import PersistentIdentifier

    obj = PersistentIdentifier.get(pid_type, pid_value)
    if obj.has_object():
        click.echo("{0.object_type} {0.object_uuid} {0.status}".format(obj))


@pid.command("dereference")
@click.argument("object_type")
@click.argument("object_uuid")
@click.option("-s", "--status", default=None, callback=process_status)
@with_appcontext
def dereference_object(object_type, object_uuid, status):
    """Show linked persistent identifier(s)."""
    from .models import PersistentIdentifier

    pids = PersistentIdentifier.query.filter_by(
        object_type=object_type, object_uuid=object_uuid
    )
    if status:
        pids = pids.filter_by(status=status)

    for found_pid in pids.all():
        click.echo("{0.pid_type} {0.pid_value} {0.pid_provider}".format(found_pid))
