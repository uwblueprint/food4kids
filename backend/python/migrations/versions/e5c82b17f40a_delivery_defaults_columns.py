"""Add the columns the Delivery Defaults tab configures

* ``support_phone`` -- the number drivers call for help mid-delivery, distinct
  from ``contact_phone``, which is the org's public number in the email footer.
* ``import_fields`` -- the spreadsheet columns the importer expects, as editable
  config. Backfilled with the set that was hardcoded in the frontend, so the
  import flow behaves identically after this runs.
* ``locations.custom_fields`` -- values for admin-defined import columns. The
  built-in columns keep their own fields; anything added in Settings lands here.

Revision ID: e5c82b17f40a
Revises: d41b6c9f2a73
Create Date: 2026-10-15 00:00:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5c82b17f40a"
down_revision = "d41b6c9f2a73"
branch_labels = None
depends_on = None


def _field(key, label, data_type, required):
    return {
        "key": key,
        "label": label,
        "data_type": data_type,
        "required": required,
        "delivery_types": [],
        "builtin": True,
    }


# Mirrors app.models.system_settings.default_import_fields. Inlined rather than
# imported: a migration has to keep describing the schema at this revision even
# after the model moves on.
DEFAULT_IMPORT_FIELDS = [
    _field("contact_name", "School Name / Last Name", "Text", True),
    _field("guardian_name", "Guardian Name", "Text", False),
    _field("address", "Address", "Address", True),
    _field("delivery_group", "Delivery Group", "Text", True),
    _field("phone_primary", "Phone Number", "Phone Number", True),
    _field("phone_secondary", "Secondary Phone Number", "Phone Number", False),
    _field("num_children", "Number of Children", "Number", False),
    _field("dietary_restrictions", "Food Restrictions", "Text", False),
    _field("halal", "Halal?", "Yes/No", False),
]


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column("support_phone", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "system_settings",
        sa.Column(
            "import_fields",
            sa.JSON(),
            nullable=False,
            server_default=json.dumps(DEFAULT_IMPORT_FIELDS),
        ),
    )
    op.add_column(
        "locations",
        sa.Column(
            "custom_fields", sa.JSON(), nullable=False, server_default="{}"
        ),
    )


def downgrade() -> None:
    op.drop_column("locations", "custom_fields")
    op.drop_column("system_settings", "import_fields")
    op.drop_column("system_settings", "support_phone")
