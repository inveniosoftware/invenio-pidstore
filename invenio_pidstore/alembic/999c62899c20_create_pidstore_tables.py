# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create pidstore tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "999c62899c20"
down_revision = "f615cee99600"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "pidstore_pid",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pid_type", sa.String(length=6), nullable=False),
        sa.Column("pid_value", sa.String(length=255), nullable=False),
        sa.Column("pid_provider", sa.String(length=8), nullable=True),
        sa.Column("status", sa.CHAR(1), nullable=False),
        sa.Column("object_type", sa.String(length=3), nullable=True),
        sa.Column("object_uuid", sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_object", "pidstore_pid", ["object_type", "object_uuid"], unique=False
    )
    op.create_index("idx_status", "pidstore_pid", ["status"], unique=False)
    op.create_index(
        "uidx_type_pid", "pidstore_pid", ["pid_type", "pid_value"], unique=True
    )
    op.create_table(
        "pidstore_recid",
        sa.Column("recid", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("recid"),
    )
    op.create_table(
        "pidstore_redirect",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("pid_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pid_id"], ["pidstore_pid.id"], onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("pidstore_redirect")
    op.drop_table("pidstore_recid")
    op.drop_index("uidx_type_pid", table_name="pidstore_pid")
    op.drop_index("idx_status", table_name="pidstore_pid")
    op.drop_index("idx_object", table_name="pidstore_pid")
    op.drop_table("pidstore_pid")
