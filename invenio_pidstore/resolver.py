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

"""Internal resolver for persistent identifiers."""

from __future__ import absolute_import, print_function

from flask import current_app
from sqlalchemy.orm.exc import NoResultFound

from .errors import PIDDeletedError, PIDMissingObjectError, \
    PIDRedirectedError, PIDUnregistered
from .models import PersistentIdentifier


class Resolver(object):
    """Persistent identifier resolver.

    Helper class for retrieving an internal object for a given persistent
    identifier.
    """

    def __init__(self, pid_type=None, object_type=None, getter=None):
        """Initialize resolver.

        :param pid_type: Persistent identifier type.
        :param object_type: Object type.
        :param getter: Callable that will take an object id for the given
            object type and retrieve the internal object.
        """
        self.pid_type = pid_type
        self.object_type = object_type
        self.object_getter = getter

    def resolve(self, pid_value):
        """Resolve a persistent identifier to an internal object.

        :param pid_value: Persistent identifier.
        """
        pid = PersistentIdentifier.get(self.pid_type, pid_value)

        if pid.is_new() or pid.is_reserved():
            raise PIDUnregistered(pid)

        if pid.is_deleted():
            obj_id = pid.get_assigned_object(object_type=self.object_type)
            try:
                obj = self.object_getter(obj_id) if obj_id else None
            except NoResultFound:
                obj = None
            raise PIDDeletedError(pid, obj)

        if pid.is_redirected():
            raise PIDRedirectedError(pid, pid.get_redirect())

        obj_id = pid.get_assigned_object(object_type=self.object_type)
        if not obj_id:
            raise PIDMissingObjectError(self.pid_type, pid_value)

        return pid, self.object_getter(obj_id)
