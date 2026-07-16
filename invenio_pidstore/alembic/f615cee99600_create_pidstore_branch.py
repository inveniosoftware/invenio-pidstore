# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Create pidstore branch."""

# revision identifiers, used by Alembic.
revision = "f615cee99600"
down_revision = None
branch_labels = ("invenio_pidstore",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
