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

from datacite import DataCiteMDSClient
from datacite.errors import (
    DataCiteError,
    DataCiteGoneError,
    DataCiteNoContentError,
    DataCiteNotFoundError,
    HttpError,
)
from flask import current_app

from ..models import PIDStatus, logger
from .base import BaseProvider


class DataCiteProvider(BaseProvider):
    """DOI provider using DataCite API."""

    pid_type = "doi"
    """Default persistent identifier type."""

    pid_provider = "datacite"
    """Persistent identifier provider name."""

    default_status = PIDStatus.NEW
    """Default status for newly created PIDs by this provider."""

    @classmethod
    def create(cls, pid_value, **kwargs):
        """Create a new record identifier.

        For more information about parameters,
        see :meth:`invenio_pidstore.providers.base.BaseProvider.create`.

        :param pid_value: Persistent identifier value.
        :params ``**kwargs``: See
            :meth:`invenio_pidstore.providers.base.BaseProvider.create` extra
            parameters.
        :returns: A
            :class:`invenio_pidstore.providers.datacite.DataCiteProvider`
            instance.
        """
        return super(DataCiteProvider, cls).create(pid_value=pid_value, **kwargs)

    def __init__(self, pid, client=None, **kwargs):
        """Initialize provider.

        To use the default client, just configure the following variables:

        * `PIDSTORE_DATACITE_USERNAME` as username.

        * `PIDSTORE_DATACITE_PASSWORD` as password.

        * `PIDSTORE_DATACITE_DOI_PREFIX` as DOI prefix.

        * `PIDSTORE_DATACITE_TESTMODE` to `True` if it configured in test mode.

        * `PIDSTORE_DATACITE_URL` as DataCite URL.

        :param pid: A :class:`invenio_pidstore.models.PersistentIdentifier`
            instance.
        :param client: A client to access to DataCite.
            (Default: :class:`datacite.DataCiteMDSClient` instance)
        """
        super(DataCiteProvider, self).__init__(pid)
        if client is not None:
            self.api = client
        else:
            self.api = DataCiteMDSClient(
                username=current_app.config.get("PIDSTORE_DATACITE_USERNAME"),
                password=current_app.config.get("PIDSTORE_DATACITE_PASSWORD"),
                prefix=current_app.config.get("PIDSTORE_DATACITE_DOI_PREFIX"),
                test_mode=current_app.config.get("PIDSTORE_DATACITE_TESTMODE", False),
                url=current_app.config.get("PIDSTORE_DATACITE_URL"),
            )

    def reserve(self, doc):
        """Reserve a DOI (amounts to upload metadata, but not to mint).

        :param doc: Set metadata for DOI.
        :returns: `True` if is reserved successfully.
        """
        # Only registered PIDs can be updated.
        try:
            self.pid.reserve()
            self.api.metadata_post(doc)
        except (DataCiteError, HttpError):
            logger.exception("Failed to reserve in DataCite", extra=dict(pid=self.pid))
            raise
        logger.info("Successfully reserved in DataCite", extra=dict(pid=self.pid))
        return True

    def register(self, url, doc):
        """Register a DOI via the DataCite API.

        :param url: Specify the URL for the API.
        :param doc: Set metadata for DOI.
        :returns: `True` if is registered successfully.
        """
        try:
            self.pid.register()
            # Set metadata for DOI
            self.api.metadata_post(doc)
            # Mint DOI
            self.api.doi_post(self.pid.pid_value, url)
        except (DataCiteError, HttpError):
            logger.exception("Failed to register in DataCite", extra=dict(pid=self.pid))
            raise
        logger.info("Successfully registered in DataCite", extra=dict(pid=self.pid))
        return True

    def update(self, url, doc):
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.

        :param doc: Set metadata for DOI.
        :returns: `True` if is updated successfully.
        """
        if self.pid.is_deleted():
            logger.info("Reactivate in DataCite", extra=dict(pid=self.pid))

        try:
            # Set metadata
            self.api.metadata_post(doc)
            self.api.doi_post(self.pid.pid_value, url)
        except (DataCiteError, HttpError):
            logger.exception("Failed to update in DataCite", extra=dict(pid=self.pid))
            raise

        if self.pid.is_deleted():
            self.pid.sync_status(PIDStatus.REGISTERED)
        logger.info("Successfully updated in DataCite", extra=dict(pid=self.pid))
        return True

    def delete(self):
        """Delete a registered DOI.

        If the PID is new then it's deleted only locally.
        Otherwise, also it's deleted also remotely.

        :returns: `True` if is deleted successfully.
        """
        try:
            if self.pid.is_new():
                self.pid.delete()
            else:
                self.pid.delete()
                self.api.metadata_delete(self.pid.pid_value)
        except (DataCiteError, HttpError):
            logger.exception("Failed to delete in DataCite", extra=dict(pid=self.pid))
            raise
        logger.info("Successfully deleted in DataCite", extra=dict(pid=self.pid))
        return True

    def sync_status(self):
        """Synchronize DOI status DataCite MDS.

        :returns: `True` if is sync successfully.
        """
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
            logger.exception(
                "Failed to sync status from DataCite", extra=dict(pid=self.pid)
            )
            raise

        if status is None:
            status = PIDStatus.NEW

        self.pid.sync_status(status)

        logger.info(
            "Successfully synced status from DataCite", extra=dict(pid=self.pid)
        )
        return True
