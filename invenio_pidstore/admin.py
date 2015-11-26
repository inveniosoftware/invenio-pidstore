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

"""Admin model views for PersistentIdentifier and PidLog."""

from flask_admin.contrib.sqla import ModelView
from flask_babelex import gettext as _

from .models import PersistentIdentifier, PIDStatus, Redirect


class PersistentIdentifierModelView(ModelView):
    """ModelView for the PersistentIdentifier."""

    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_list = (
        'id', 'pid_type', 'pid_value', 'pid_provider', 'status', 'object_type',
        'object_uuid', 'last_modified',
    )
    column_searchable_list = ('pid_value', )
    form_choices = {
        'status': ((PIDStatus.NEW, _('New')),
                   (PIDStatus.RESERVED, _('Reserved')),
                   (PIDStatus.REGISTERED, _('Registered')),
                   (PIDStatus.DELETED, _('Inactive')))
    }
    """
    PIDStatus form choices in the typical lifetime order.
    """


class RedirectModelView(ModelView):
    """ModelView for the Redirect."""

    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True
    column_list = ('id', 'pid_id', 'pid',)


pid_adminview = dict(modelview=PersistentIdentifierModelView,
                     model=PersistentIdentifier,
                     category='PIDStore')
redirect_adminview = dict(modelview=RedirectModelView,
                          model=Redirect,
                          category='PIDStore')

__all__ = (
    'pid_adminview',
    'redirect_adminview',
)
