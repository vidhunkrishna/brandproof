"""store review mode with immutable submission revisions

Revision ID: f3303cabb192
Revises: 82a2d7e1e698
Create Date: 2026-11-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f3303cabb192"
down_revision: Union[str, Sequence[str], None] = "82a2d7e1e698"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Retain whether the advisory analyzer used its deterministic fallback."""
    op.add_column("submission_revisions", sa.Column("review_used_fallback", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("submission_revisions", "review_used_fallback")
