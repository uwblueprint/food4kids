"""drop unused entity and simple_entity tables

These were starter-template boilerplate (sample CRUD with no business use).
Their models, routers, and services have been removed, so drop the tables and
their now-orphaned enum types.

Revision ID: d12a38cacf7c
Revises: f3b1c9a2d4e7
Create Date: 2026-05-26 20:15:07.966749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd12a38cacf7c'
down_revision = 'f3b1c9a2d4e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("simple_entities")
    op.drop_table("entities")
    op.execute(sa.text("DROP TYPE IF EXISTS entityenum"))
    op.execute(sa.text("DROP TYPE IF EXISTS simpleentityenum"))


def downgrade() -> None:
    # Mirrors the original create_table in 001_initial_schema (string_field is
    # a plain String; its max_length was a Pydantic validator, not a DB type).
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("string_field", sa.String(), nullable=False),
        sa.Column("int_field", sa.Integer(), nullable=False),
        sa.Column(
            "enum_field",
            sa.Enum("A", "B", "C", "D", name="entityenum"),
            nullable=False,
        ),
        sa.Column("string_array_field", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("bool_field", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "simple_entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("string_field", sa.String(), nullable=False),
        sa.Column("int_field", sa.Integer(), nullable=False),
        sa.Column(
            "enum_field",
            sa.Enum("A", "B", "C", "D", name="simpleentityenum"),
            nullable=False,
        ),
        sa.Column("string_array_field", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("bool_field", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
