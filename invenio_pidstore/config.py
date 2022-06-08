# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-PIDStore configuration."""

PIDSTORE_RECID_FIELD = "control_number"
"""Default record id field inside the json data.

This name will be used by the fetcher, to retrieve the record ID value from the
JSON, and by the minter, to store it inside the JSON.
"""


PIDSTORE_DATACITE_DOI_PREFIX = ""
"""Provide a DOI prefix here."""

PIDSTORE_RECORDID_OPTIONS = {"length": 10, "split_every": 5, "checksum": True}
