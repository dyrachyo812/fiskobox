"""add extraction confidence metadata

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-02 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "low_quality_scan",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column("sharpness_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("amount_matched_by", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("date_matched_by", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("merchant_matched_by", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column(
            "needs_manual_review",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("receipts", "needs_manual_review")
    op.drop_column("receipts", "merchant_matched_by")
    op.drop_column("receipts", "date_matched_by")
    op.drop_column("receipts", "amount_matched_by")
    op.drop_column("documents", "sharpness_score")
    op.drop_column("documents", "low_quality_scan")
