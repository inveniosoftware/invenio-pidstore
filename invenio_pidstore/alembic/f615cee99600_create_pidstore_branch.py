# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create pidstore branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f615cee99600"
down_revision = None
branch_labels = ("invenio_pidstore",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
