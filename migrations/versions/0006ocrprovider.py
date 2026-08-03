"""add ocr provider metadata

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-02 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("ocr_provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "ocr_confidence")
    op.drop_column("documents", "ocr_provider")
