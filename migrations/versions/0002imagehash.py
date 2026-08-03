"""add image_hash to documents

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-02 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("image_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_documents_image_hash", "documents", ["image_hash"])


def downgrade() -> None:
    op.drop_index("ix_documents_image_hash", table_name="documents")
    op.drop_column("documents", "image_hash")
