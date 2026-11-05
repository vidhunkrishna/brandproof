"""add visual brand compliance
Revision ID: d4e7f1a9c625
Revises: c9f2a6e8b413
"""
from alembic import op
import sqlalchemy as sa
revision="d4e7f1a9c625"; down_revision="c9f2a6e8b413"; branch_labels=None; depends_on=None
def upgrade():
 op.create_table("visual_brand_configs",sa.Column("id",sa.String(36),primary_key=True),sa.Column("organization_id",sa.String(36),sa.ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False,unique=True),sa.Column("approved_colors",sa.JSON(),nullable=False),sa.Column("approved_fonts",sa.JSON(),nullable=False),sa.Column("primary_logo_aspect_ratio",sa.Float()),sa.Column("secondary_logo_aspect_ratio",sa.Float()),sa.Column("minimum_contrast_ratio",sa.Float(),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False))
 op.create_table("visual_asset_reviews",sa.Column("id",sa.String(36),primary_key=True),sa.Column("organization_id",sa.String(36),sa.ForeignKey("organizations.id",ondelete="CASCADE"),nullable=False),sa.Column("created_by_user_id",sa.String(36),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("filename",sa.String(255),nullable=False),sa.Column("content_type",sa.String(100),nullable=False),sa.Column("byte_size",sa.Integer(),nullable=False),sa.Column("width",sa.Integer(),nullable=False),sa.Column("height",sa.Integer(),nullable=False),sa.Column("detected_format",sa.String(20),nullable=False),sa.Column("findings_json",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False))
 op.create_index("ix_visual_asset_reviews_organization_id","visual_asset_reviews",["organization_id"])
def downgrade():
 op.drop_index("ix_visual_asset_reviews_organization_id",table_name="visual_asset_reviews");op.drop_table("visual_asset_reviews");op.drop_table("visual_brand_configs")
