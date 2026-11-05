"""add guideline governance metadata

Revision ID: b7e8c1d4f902
Revises: e6d4b9c2a701
Create Date: 2026-11-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "b7e8c1d4f902"
down_revision: Union[str, Sequence[str], None] = "e6d4b9c2a701"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("guidelines", sa.Column("scope", sa.String(length=255), nullable=True))
    op.add_column("guidelines", sa.Column("owner_user_id", sa.String(length=36), nullable=True))
    op.add_column("guidelines", sa.Column("review_due_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_guidelines_owner_user", "guidelines", "users", ["owner_user_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    op.drop_constraint("fk_guidelines_owner_user", "guidelines", type_="foreignkey")
    op.drop_column("guidelines", "review_due_at")
    op.drop_column("guidelines", "owner_user_id")
    op.drop_column("guidelines", "scope")
