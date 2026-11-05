from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin

class VisualBrandConfig(Base, TimestampMixin):
    __tablename__ = "visual_brand_configs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    approved_colors = Column(JSON, nullable=False, default=list)
    approved_fonts = Column(JSON, nullable=False, default=list)
    primary_logo_aspect_ratio = Column(Float, nullable=True)
    secondary_logo_aspect_ratio = Column(Float, nullable=True)
    minimum_contrast_ratio = Column(Float, nullable=False, default=4.5)

class VisualAssetReview(Base, TimestampMixin):
    __tablename__ = "visual_asset_reviews"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    byte_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    detected_format = Column(String(20), nullable=False)
    findings_json = Column(JSON, nullable=False, default=list)
    organization = relationship("Organization")
