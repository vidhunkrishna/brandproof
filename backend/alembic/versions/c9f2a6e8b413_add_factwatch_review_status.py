"""add FactWatch review status

Revision ID: c9f2a6e8b413
Revises: b7e8c1d4f902
"""
from alembic import op
import sqlalchemy as sa
revision = "c9f2a6e8b413"
down_revision = "b7e8c1d4f902"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("approved_facts", sa.Column("review_status", sa.String(30), nullable=False, server_default="pending"))
    op.add_column("approved_facts", sa.Column("reviewed_by_user_id", sa.String(36), nullable=True))
    op.add_column("approved_facts", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_facts_reviewer", "approved_facts", "users", ["reviewed_by_user_id"], ["id"], ondelete="SET NULL")
def downgrade():
    op.drop_constraint("fk_facts_reviewer", "approved_facts", type_="foreignkey")
    op.drop_column("approved_facts", "reviewed_at"); op.drop_column("approved_facts", "reviewed_by_user_id"); op.drop_column("approved_facts", "review_status")
