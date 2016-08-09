# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Click command-line interface for PIDStore management."""

from __future__ import absolute_import, print_function

import json
import sys

import click
from invenio_db import db
from sqlalchemy.exc import StatementError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import cached_property, import_string

from .proxies import current_pidstore

try:
    from flask.cli import with_appcontext
except ImportError:
    from flask_cli import with_appcontext


def loader_import(ctx, param, value):
    """Import the loader."""
    if value:
        try:
            return import_string(value)
        except ImportError:
            raise click.BadParameter('Loader {0} not found.'.format(value))


class LazyMinter(object):
    """Lazy minter."""

    def __init__(self, ctx, param, value):
        """Init."""
        self.value = value

    @cached_property
    def minter(self):
        """Get minter."""
        try:
            return current_pidstore.minters[self.value]
        except KeyError:
            raise click.BadParameter(
                param_hint='minter',
                message='Unknown minter {0}. Please use one of: {1}.'.format(
                    self.value, ', '.join(current_pidstore.minters.keys())
                )
            )

    def __call__(self, *args, **kwargs):
        """Call."""
        return self.minter(*args, **kwargs)


def process_status(ctx, param, value):
    """Return status value."""
    from .models import PIDStatus

    # Allow empty status
    if value is None:
        return None

    if not hasattr(PIDStatus, value):
        raise click.BadParameter('Status needs to be one of {0}.'.format(
            ', '.join([s.name for s in PIDStatus])
        ))
    return getattr(PIDStatus, value)


#
# PIDStore management commands
#

@click.group()
def pid():
    """PID-Store management commands."""


@pid.command()
@click.argument('pid_type')
@click.argument('pid_value')
@click.option('-s', '--status', default='NEW', callback=process_status)
@click.option('-t', '--type', 'object_type', default=None)
@click.option('-i', '--uuid', 'object_uuid', default=None)
@with_appcontext
def create(pid_type, pid_value, status, object_type, object_uuid):
    """Create new persistent identifier."""
    from .models import PersistentIdentifier

    if bool(object_type) ^ bool(object_uuid):
        raise click.BadParameter('Speficy both or any of --type and --uuid.')

    new_pid = PersistentIdentifier.create(
        pid_type,
        pid_value,
        status=status,
        object_type=object_type,
        object_uuid=object_uuid,
    )
    db.session.commit()
    click.echo(
        '{0.pid_type} {0.pid_value} {0.pid_provider}'.format(new_pid)
    )


@pid.command()
@click.argument('pid_type')
@click.argument('pid_value')
@click.option('-s', '--status', default=None, callback=process_status)
@click.option('-t', '--type', 'object_type', required=True)
@click.option('-i', '--uuid', 'object_uuid', required=True)
@click.option('--overwrite', is_flag=True, default=False)
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
@click.argument('pid_type')
@click.argument('pid_value')
@with_appcontext
def unassign(pid_type, pid_value):
    """Unassign persistent identifier."""
    from .models import PersistentIdentifier

    obj = PersistentIdentifier.get(pid_type, pid_value)
    obj.unassign()
    db.session.commit()
    click.echo(obj.status)


@pid.command('get')
@click.argument('pid_type')
@click.argument('pid_value')
@with_appcontext
def get_object(pid_type, pid_value):
    """Get an object behind persistent identifier."""
    from .models import PersistentIdentifier

    obj = PersistentIdentifier.get(pid_type, pid_value)
    if obj.has_object():
        click.echo('{0.object_type} {0.object_uuid} {0.status}'.format(obj))


@pid.command('dereference')
@click.argument('object_type')
@click.argument('object_uuid')
@click.option('-s', '--status', default=None, callback=process_status)
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
        click.echo(
            '{0.pid_type} {0.pid_value} {0.pid_provider}'.format(found_pid)
        )


@pid.command()
@click.argument('minter', callback=LazyMinter)
@click.argument('ids', nargs=-1)
@click.option('-l', '--loader',
              default=None,
              callback=loader_import)
@with_appcontext
def mint(minter, ids, loader):
    """Mint objects."""
    objects = []
    if loader:
        for id_ in ids:
            try:
                data = loader(id_)
                minter(id_, data)
                objects.append(data)
            except (StatementError, NoResultFound) as e:
                click.echo(
                    'Error for the object id {0}: {1}'.format(id_, e), err=True
                )
    else:
        data = json.load(sys.stdin)
        if isinstance(data, dict):
            data = [data]
        for obj in data:
            minter(None, obj)
            objects.append(obj)

    db.session.commit()
    click.echo(json.dumps(objects, sort_keys=True, indent=4))
