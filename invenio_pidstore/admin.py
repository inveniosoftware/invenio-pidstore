# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for PersistentIdentifier."""

import uuid

from flask import current_app, url_for
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual
from markupsafe import Markup

from .models import PersistentIdentifier, PIDStatus


def _(x):
    """Identity function for string extraction."""
    return x


def object_formatter(v, c, m, p):
    """Format object view link."""
    endpoint = current_app.config["PIDSTORE_OBJECT_ENDPOINTS"].get(m.object_type)

    if endpoint and m.object_uuid:
        return Markup(
            '<a href="{0}">{1}</a>'.format(
                url_for(endpoint, id=m.object_uuid), _("View")
            )
        )
    return ""


class FilterUUID(FilterEqual):
    """UUID aware filter."""

    def apply(self, query, value, alias):
        """Convert UUID."""
        return query.filter(self.column == uuid.UUID(value))


class PersistentIdentifierModelView(ModelView):
    """ModelView for the PersistentIdentifier."""

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_display_all_relations = True
    column_list = (
        "pid_type",
        "pid_value",
        "status",
        "object_type",
        "object_uuid",
        "created",
        "updated",
        "object",
    )
    column_labels = dict(
        pid_type=_("PID Type"),
        pid_value=_("PID"),
        pid_provider=_("Provider"),
        status=_("Status"),
        object_type=_("Object Type"),
        object_uuid=_("Object UUID"),
    )
    column_filters = (
        "pid_type",
        "pid_value",
        "object_type",
        FilterUUID(PersistentIdentifier.object_uuid, _("Object UUID")),
        FilterEqual(
            PersistentIdentifier.status,
            _("Status"),
            options=[(s.value, s.title) for s in PIDStatus],
        ),
    )
    column_searchable_list = ("pid_value",)
    column_default_sort = ("updated", True)
    column_formatters = dict(object=object_formatter)
    page_size = 25


pid_adminview = dict(
    modelview=PersistentIdentifierModelView,
    model=PersistentIdentifier,
    category=_("Records"),
)
