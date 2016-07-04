# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""Persistent identifier store and registration."""

from __future__ import absolute_import, print_function

import logging
import uuid
from enum import Enum

import six
from flask_babelex import gettext
from invenio_db import db
from speaklater import make_lazy_gettext
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import ChoiceType, UUIDType

from .errors import PIDAlreadyExists, PIDDoesNotExistError, PIDInvalidAction, \
    PIDObjectAlreadyAssigned

_ = make_lazy_gettext(lambda: gettext)

logger = logging.getLogger('invenio-pidstore')


PID_STATUS_TITLES = {
    'NEW': _('New'),
    'RESERVED': _('Reserved'),
    'REGISTERED': _('Registered'),
    'REDIRECTED': _('Redirected'),
    'DELETED': _('Deleted'),
}


class PIDStatus(Enum):
    """Constants for possible status of any given PID."""

    __order__ = 'NEW RESERVED REGISTERED REDIRECTED DELETED'

    NEW = 'N'
    """PID has *not* yet been registered with the service provider."""

    RESERVED = 'K'
    """PID reserved in the service provider but not yet fully registered."""

    REGISTERED = 'R'
    """PID has been registered with the service provider."""

    REDIRECTED = 'M'
    """PID has been redirected to another persistent identifier."""

    DELETED = 'D'
    """PID has been deleted/inactivated with the service provider.

    This should happen very rarely, and must be kept track of, as the PID
    should not be reused for something else.
    """

    def __init__(self, value):
        """Hack."""

    def __eq__(self, other):
        """Equality test."""
        return self.value == other

    def __str__(self):
        """Return its value."""
        return self.value

    @property
    def title(self):
        """Return human readable title."""
        return PID_STATUS_TITLES[self.name]


class PersistentIdentifier(db.Model, Timestamp):
    """Store and register persistent identifiers.

    Assumptions:
      * Persistent identifiers can be represented as a string of max 255 chars.
      * An object has many persistent identifiers.
      * A persistent identifier has one and only one object.
    """

    __tablename__ = 'pidstore_pid'
    __table_args__ = (
        db.Index('uidx_type_pid', 'pid_type', 'pid_value', unique=True),
        db.Index('idx_status', 'status'),
        db.Index('idx_object', 'object_type', 'object_uuid'),
    )

    id = db.Column(db.Integer, primary_key=True)
    """Id of persistent identifier entry."""

    pid_type = db.Column(db.String(6), nullable=False)
    """Persistent Identifier Schema."""

    pid_value = db.Column(db.String(255), nullable=False)
    """Persistent Identifier."""

    pid_provider = db.Column(db.String(8), nullable=True)
    """Persistent Identifier Provider"""

    status = db.Column(ChoiceType(PIDStatus, impl=db.CHAR(1)), nullable=False)
    """Status of persistent identifier, e.g. registered, reserved, deleted."""

    object_type = db.Column(db.String(3), nullable=True)
    """Object Type - e.g. rec for record."""

    object_uuid = db.Column(UUIDType, nullable=True)
    """Object ID - e.g. a record id."""

    #
    # Class methods
    #
    @classmethod
    def create(cls, pid_type, pid_value, pid_provider=None,
               status=PIDStatus.NEW, object_type=None, object_uuid=None,):
        """Create a new persistent identifier with specific type and value.

        :param pid_type: Persistent identifier type.
        :param pid_value: Persistent identifier value.
        """
        try:
            with db.session.begin_nested():
                obj = cls(pid_type=pid_type,
                          pid_value=pid_value,
                          pid_provider=pid_provider,
                          status=status)
                if object_type and object_uuid:
                    obj.assign(object_type, object_uuid)
                db.session.add(obj)
            logger.info("Created PID {0}:{1}".format(pid_type, pid_value),
                        extra={'pid': obj})
        except IntegrityError:
            logger.exception(
                "PID already exists: {0}:{1}".format(pid_type, pid_value),
                extra=dict(
                    pid_type=pid_type,
                    pid_value=pid_value,
                    pid_provider=pid_provider,
                    status=status,
                    object_type=object_type,
                    object_uuid=object_uuid,
                ))
            raise PIDAlreadyExists(pid_type=pid_type, pid_value=pid_value)
        except SQLAlchemyError:
            logger.exception(
                "Failed to create PID: {0}:{1}".format(pid_type, pid_value),
                extra=dict(
                    pid_type=pid_type,
                    pid_value=pid_value,
                    pid_provider=pid_provider,
                    status=status,
                    object_type=object_type,
                    object_uuid=object_uuid,
                ))
            raise
        return obj

    @classmethod
    def get(cls, pid_type, pid_value, pid_provider=None):
        """Get persistent identifier."""
        try:
            args = dict(pid_type=pid_type, pid_value=six.text_type(pid_value))
            if pid_provider:
                args['pid_provider'] = pid_provider
            return cls.query.filter_by(**args).one()
        except NoResultFound:
            raise PIDDoesNotExistError(pid_type, pid_value)

    @classmethod
    def get_by_object(cls, pid_type, object_type, object_uuid):
        """Get a persistent identifier for a given object."""
        try:
            return cls.query.filter_by(
                pid_type=pid_type,
                object_type=object_type,
                object_uuid=object_uuid
            ).one()
        except NoResultFound:
            raise PIDDoesNotExistError(pid_type, None)

    #
    # Assigned object methods
    #
    def has_object(self):
        """Determine if this PID has an assigned object."""
        return bool(self.object_type and self.object_uuid)

    def get_assigned_object(self, object_type=None):
        """Return an assigned object."""
        if object_type is not None:
            if self.object_type == object_type:
                return self.object_uuid
            else:
                return None
        return self.object_uuid

    def assign(self, object_type, object_uuid, overwrite=False):
        """Assign this persistent identifier to a given object.

        Note, the persistent identifier must first have been reserved. Also,
        if an existing object is already assigned to the pid, it will raise an
        exception unless overwrite=True.
        """
        if self.is_deleted():
            raise PIDInvalidAction(
                "You cannot assign objects to a deleted/redirected persistent"
                " identifier."
            )

        if not isinstance(object_uuid, uuid.UUID):
            object_uuid = uuid.UUID(object_uuid)

        if self.object_type or self.object_uuid:
            # The object is already assigned to this pid.
            if object_type == self.object_type and \
               object_uuid == self.object_uuid:
                return True
            if not overwrite:
                raise PIDObjectAlreadyAssigned(object_type,
                                               object_uuid)
            self.unassign()

        try:
            with db.session.begin_nested():
                self.object_type = object_type
                self.object_uuid = object_uuid
                db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to assign {0}:{1}".format(
                object_type, object_uuid), extra=dict(pid=self))
            raise
        logger.info("Assigned object {0}:{1}".format(
            object_type, object_uuid), extra=dict(pid=self))
        return True

    def unassign(self):
        """Unassign the registered object."""
        if self.object_uuid is None and self.object_type is None:
            return True

        try:
            with db.session.begin_nested():
                if self.is_redirected():
                    db.session.delete(Redirect.query.get(self.object_uuid))
                    # Only registered PIDs can be redirected so we set it back
                    # to registered
                    self.status = PIDStatus.REGISTERED
                self.object_type = None
                self.object_uuid = None
                db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to unassign object.".format(self),
                             extra=dict(pid=self))
            raise
        logger.info("Unassigned object from {0}.".format(self),
                    extra=dict(pid=self))
        return True

    def get_redirect(self):
        """Get redirected persistent identifier."""
        return Redirect.query.get(self.object_uuid).pid

    #
    # Status methods.
    #
    def redirect(self, pid):
        """Redirect persistent identifier to another persistent identifier."""
        if not (self.is_registered() or self.is_redirected()):
            raise PIDInvalidAction("Persistent identifier is not registered.")

        try:
            with db.session.begin_nested():
                if self.is_redirected():
                    r = Redirect.query.get(self.object_uuid)
                    r.pid = pid
                else:
                    with db.session.begin_nested():
                        r = Redirect(pid=pid)
                        db.session.add(r)

                self.status = PIDStatus.REDIRECTED
                self.object_type = None
                self.object_uuid = r.id
                db.session.add(self)
        except IntegrityError:
            raise PIDDoesNotExistError(pid.pid_type, pid.pid_value)
        except SQLAlchemyError:
            logger.exception("Failed to redirect to {0}".format(
                pid), extra=dict(pid=self))
            raise
        logger.info("Redirected PID to {0}".format(pid), extra=dict(pid=self))
        return True

    def reserve(self):
        """Reserve the persistent identifier.

        Note, the reserve method may be called multiple times, even if it was
        already reserved.
        """
        if not (self.is_new() or self.is_reserved()):
            raise PIDInvalidAction(
                "Persistent identifier is not new or reserved.")

        try:
            with db.session.begin_nested():
                self.status = PIDStatus.RESERVED
                db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to reserve PID.", extra=dict(pid=self))
            raise
        logger.info("Reserved PID.", extra=dict(pid=self))
        return True

    def register(self):
        """Register the persistent identifier with the provider."""
        if self.is_registered() or self.is_deleted() or self.is_redirected():
            raise PIDInvalidAction(
                "Persistent identifier has already been registered"
                " or is deleted.")

        try:
            with db.session.begin_nested():
                self.status = PIDStatus.REGISTERED
                db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to register PID.", extra=dict(pid=self))
            raise
        logger.info("Registered PID.", extra=dict(pid=self))
        return True

    def delete(self):
        """Delete the persistent identifier."""
        removed = False
        try:
            with db.session.begin_nested():
                if self.is_new():
                    # New persistent identifier which haven't been registered
                    # yet.
                    db.session.delete(self)
                    removed = True
                else:
                    self.status = PIDStatus.DELETED
                    db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to delete PID.", extra=dict(pid=self))
            raise

        if removed:
            logger.info("Deleted PID (removed).", extra=dict(pid=self))
        else:
            logger.info("Deleted PID.", extra=dict(pid=self))
        return True

    def sync_status(self, status):
        """Synchronize persistent identifier status.

        Used when the provider uses an external service, which might have been
        modified outside of our system.
        """
        if self.status == status:
            return True

        try:
            with db.session.begin_nested():
                self.status = status
                db.session.add(self)
        except SQLAlchemyError:
            logger.exception("Failed to sync status {0}.".format(status),
                             extra=dict(pid=self))
            raise
        logger.info("Synced PID status to {0}.".format(status),
                    extra=dict(pid=self))
        return True

    def is_redirected(self):
        """Return true if the persistent identifier has been registered."""
        return self.status == PIDStatus.REDIRECTED

    def is_registered(self):
        """Return true if the persistent identifier has been registered."""
        return self.status == PIDStatus.REGISTERED

    def is_deleted(self):
        """Return true if the persistent identifier has been deleted."""
        return self.status == PIDStatus.DELETED

    def is_new(self):
        """Return true if the PIDhas not yet been registered or reserved."""
        return self.status == PIDStatus.NEW

    def is_reserved(self):
        """Return true if the PID has not yet been reserved."""
        return self.status == PIDStatus.RESERVED

    def __repr__(self):
        """Get representation of object."""
        return "<PersistentIdentifier {0}:{1}{3} ({2})>".format(
            self.pid_type, self.pid_value, self.status,
            " / {0}:{1}".format(self.object_type, self.object_uuid) if
            self.object_type else ""
        )


class Redirect(db.Model, Timestamp):
    """Redirect for a persistent identifier."""

    __tablename__ = 'pidstore_redirect'
    id = db.Column(UUIDType, default=uuid.uuid4, primary_key=True)
    """Id of redirect entry."""

    pid_id = db.Column(
        db.Integer,
        db.ForeignKey(PersistentIdentifier.id, onupdate="CASCADE",
                      ondelete="RESTRICT"),
        nullable=False)
    """Persistent identifier."""

    pid = db.relationship(PersistentIdentifier, backref='redirects')
    """Relationship to persistent identifier."""


class RecordIdentifier(db.Model):
    """Sequence generator for integer record identifiers.

    The sole purpose of this model is to generate integer record identifiers in
    sequence using the underlying database's auto increment features in a
    transaction friendly manner. The feature is primarily provided to support
    legacy Invenio instances to continue their current record identifier
    scheme. For new instances we strong encourage to not use auto incrementing
    record identifiers, but instead use e.g. UUIDs as record identifiers.
    """

    __tablename__ = 'pidstore_recid'

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True, autoincrement=True)

    @classmethod
    def next(cls):
        """Return next available record identifier."""
        try:
            with db.session.begin_nested():
                obj = cls()
                db.session.add(obj)
        except IntegrityError:  # pragma: no cover
            with db.session.begin_nested():
                # Someone has likely modified the table without using the
                # models API. Let's fix the problem.
                cls._set_sequence(cls.max())
                obj = cls()
                db.session.add(obj)
        return obj.recid

    @classmethod
    def max(cls):
        """Get max record identifier."""
        max_recid = db.session.query(func.max(cls.recid)).scalar()
        return max_recid if max_recid else 0

    @classmethod
    def _set_sequence(cls, val):
        """Internal function to reset sequence to specific value."""
        if db.engine.dialect.name == 'postgresql':  # pragma: no cover
            db.session.execute(
                "SELECT setval(pg_get_serial_sequence("
                "'{0}', 'recid'), :newval)".format(
                    cls.__tablename__), dict(newval=val))

    @classmethod
    def insert(cls, val):
        """Insert a record identifier."""
        with db.session.begin_nested():
            obj = cls(recid=val)
            db.session.add(obj)
            cls._set_sequence(cls.max())


__all__ = (
    'PersistentIdentifier',
    'PIDStatus',
    'RecordIdentifier',
    'Redirect',
)
