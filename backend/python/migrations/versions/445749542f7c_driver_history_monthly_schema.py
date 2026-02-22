"""driver history monthly schema

Revision ID: 445749542f7c
Revises: eb010a6ed5ad
Create Date: 2026-02-21 20:11:48.832310

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '445749542f7c'
down_revision = 'eb010a6ed5ad'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("driver_history")

    op.create_table(
        "driver_history",
        sa.Column("driver_history_id", sa.Integer(), primary_key=True),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.driver_id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("km", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.UniqueConstraint("driver_id", "year", "month"),
    )

    op.create_index(
        "ix_driver_history_driver_id",
        "driver_history",
        ["driver_id"]
    )