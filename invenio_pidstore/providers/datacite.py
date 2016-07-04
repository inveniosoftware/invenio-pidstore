# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""DataCite PID provider."""

from __future__ import absolute_import

from datacite import DataCiteMDSClient
from datacite.errors import DataCiteError, DataCiteGoneError, \
    DataCiteNoContentError, DataCiteNotFoundError, HttpError
from flask import current_app

from ..models import PIDStatus, logger
from .base import BaseProvider


class DataCiteProvider(BaseProvider):
    """DOI provider using DataCite API."""

    pid_type = 'doi'
    pid_provider = 'datacite'
    default_status = PIDStatus.NEW

    @classmethod
    def create(cls, pid_value, **kwargs):
        """Create a new record identifier."""
        return super(DataCiteProvider, cls).create(
            pid_value=pid_value, **kwargs)

    def __init__(self, pid, client=None):
        """Initialize provider."""
        super(DataCiteProvider, self).__init__(pid)
        if client is not None:
            self.api = client
        else:
            self.api = DataCiteMDSClient(
                username=current_app.config.get('PIDSTORE_DATACITE_USERNAME'),
                password=current_app.config.get('PIDSTORE_DATACITE_PASSWORD'),
                prefix=current_app.config.get('PIDSTORE_DATACITE_DOI_PREFIX'),
                test_mode=current_app.config.get(
                    'PIDSTORE_DATACITE_TESTMODE', False),
                url=current_app.config.get('PIDSTORE_DATACITE_URL'))

    def reserve(self, doc):
        """Reserve a DOI (amounts to upload metadata, but not to mint)."""
        # Only registered PIDs can be updated.
        try:
            self.pid.reserve()
            self.api.metadata_post(doc)
        except (DataCiteError, HttpError):
            logger.exception("Failed to reserve in DataCite",
                             extra=dict(pid=self.pid))
            raise
        logger.info("Successfully reserved in DataCite",
                    extra=dict(pid=self.pid))
        return True

    def register(self, url, doc):
        """Register a DOI via the DataCite API."""
        try:
            self.pid.register()
            # Set metadata for DOI
            self.api.metadata_post(doc)
            # Mint DOI
            self.api.doi_post(self.pid.pid_value, url)
        except (DataCiteError, HttpError):
            logger.exception("Failed to register in DataCite",
                             extra=dict(pid=self.pid))
            raise
        logger.info("Successfully registered in DataCite",
                    extra=dict(pid=self.pid))
        return True

    def update(self, url, doc):
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.
        """
        if self.pid.is_deleted():
            logger.info("Reactivate in DataCite",
                        extra=dict(pid=self.pid))

        try:
            # Set metadata
            self.api.metadata_post(doc)
            self.api.doi_post(self.pid.pid_value, url)
        except (DataCiteError, HttpError):
            logger.exception("Failed to update in DataCite",
                             extra=dict(pid=self.pid))
            raise

        if self.pid.is_deleted():
            self.pid.sync_status(PIDStatus.REGISTERED)
        logger.info("Successfully updated in DataCite",
                    extra=dict(pid=self.pid))
        return True

    def delete(self):
        """Delete a registered DOI."""
        try:
            if self.pid.is_new():
                self.pid.delete()
            else:
                self.pid.delete()
                self.api.metadata_delete(self.pid.pid_value)
        except (DataCiteError, HttpError):
            logger.exception("Failed to delete in DataCite",
                             extra=dict(pid=self.pid))
            raise
        logger.info("Successfully deleted in DataCite",
                    extra=dict(pid=self.pid))
        return True

    def sync_status(self):
        """Synchronize DOI status DataCite MDS."""
        status = None

        try:
            try:
                self.api.doi_get(self.pid.pid_value)
                status = PIDStatus.REGISTERED
            except DataCiteGoneError:
                status = PIDStatus.DELETED
            except DataCiteNoContentError:
                status = PIDStatus.REGISTERED
            except DataCiteNotFoundError:
                pass

            if status is None:
                try:
                    self.api.metadata_get(self.pid.pid_value)
                    status = PIDStatus.RESERVED
                except DataCiteGoneError:
                    status = PIDStatus.DELETED
                except DataCiteNoContentError:
                    status = PIDStatus.REGISTERED
                except DataCiteNotFoundError:
                    pass
        except (DataCiteError, HttpError):
            logger.exception("Failed to sync status from DataCite",
                             extra=dict(pid=self.pid))
            raise

        if status is None:
            status = PIDStatus.NEW

        self.pid.sync_status(status)

        logger.info("Successfully synced status from DataCite",
                    extra=dict(pid=self.pid))
        return True
