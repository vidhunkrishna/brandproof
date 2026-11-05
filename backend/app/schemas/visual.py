from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class VisualConfigRequest(BaseModel):
    approved_colors: List[str] = Field(default_factory=list)
    approved_fonts: List[str] = Field(default_factory=list)
    primary_logo_aspect_ratio: Optional[float] = Field(None, gt=0)
    secondary_logo_aspect_ratio: Optional[float] = Field(None, gt=0)
    minimum_contrast_ratio: float = Field(4.5, ge=1, le=21)
    @field_validator("approved_colors")
    @classmethod
    def hex_colors(cls, values):
        for value in values:
            if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
                raise ValueError("Approved colors must use #RRGGBB format.")
            int(value[1:], 16)
        return [value.upper() for value in values]

class VisualConfigResponse(VisualConfigRequest):
    id: str
    organization_id: str

class VisualAssetResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    byte_size: int
    width: int
    height: int
    detected_format: str
    findings_json: list
    created_at: datetime
