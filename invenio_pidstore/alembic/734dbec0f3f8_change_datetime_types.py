# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Create pidstore tables."""

from invenio_db.utils import (
    update_table_columns_column_type_to_datetime,
    update_table_columns_column_type_to_utc_datetime,
)

# revision identifiers, used by Alembic.
revision = "734dbec0f3f8"
down_revision = "999c62899c20"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    for table_name in ["pidstore_pid", "pidstore_redirect"]:
        update_table_columns_column_type_to_utc_datetime(table_name, "created")
        update_table_columns_column_type_to_utc_datetime(table_name, "updated")


def downgrade():
    """Downgrade database."""
    for table_name in ["pidstore_pid", "pidstore_redirect"]:
        update_table_columns_column_type_to_datetime(table_name, "created")
        update_table_columns_column_type_to_datetime(table_name, "updated")
