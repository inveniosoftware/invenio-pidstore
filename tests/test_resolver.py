# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from invenio_db import db

from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver


def test_resolver(app):
    """Test the class methods of PersistentIdentifier class."""
    with app.app_context():
        # Live PID
        pid = PersistentIdentifier.create('recid', '1', 'recid')
        pid.assign('rec', '1')

        # No object pid.
        pid = PersistentIdentifier.create('recid', '3', 'recid')
        pid.register()

        # Deleted PID
        pid = PersistentIdentifier.create('recid', '2', 'recid')
        pid.assign('rec', '2')
        pid.register()
        db.session.commit()
        pid.delete()
        db.session.commit()

        resolver = Resolver(
            pid_type='recid',
            pid_provider='recid',
            obj_type='rec',
            getter=lambda x: x)

        pid, obj = resolver.resolve('1')
        assert pid
        assert obj == '1'

        pytest.raises(PIDDeletedError, resolver.resolve, '2')
        pytest.raises(PIDMissingObjectError, resolver.resolve, '3')
        pytest.raises(PIDDoesNotExistError, resolver.resolve, '4')

        doiresolver = Resolver(
            pid_type='doi',
            pid_provider='doi',
            obj_type='rec',
            getter=lambda x: x)
        pytest.raises(PIDDoesNotExistError, doiresolver.resolve, '1')
