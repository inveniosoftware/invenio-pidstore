# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Admin model views for PersistentIdentifier."""

from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual

from .models import PersistentIdentifier, PIDStatus


def _(x):
    """Identity function for string extraction."""
    return x


class PersistentIdentifierModelView(ModelView):
    """ModelView for the PersistentIdentifier."""

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_display_all_relations = True
    column_list = (
        'pid_type', 'pid_value', 'status', 'object_type',
        'object_uuid', 'created', 'updated',
    )
    column_labels = dict(
        pid_type=_('PID Type'),
        pid_value=_('PID'),
        pid_provider=_('Provider'),
        status=_('Status'),
        object_type=_('Object Type'),
        object_uuid=_('Object UUID'),
    )
    column_filters = ('pid_type', 'pid_value', 'object_type', FilterEqual(
        PersistentIdentifier.status, 'Status',
        options=[(s.value, s.title) for s in PIDStatus]
    ), )
    column_searchable_list = ('pid_value', )
    column_default_sort = ('updated', True)
    page_size = 25


pid_adminview = dict(
    modelview=PersistentIdentifierModelView,
    model=PersistentIdentifier,
    category=_('Records'))
