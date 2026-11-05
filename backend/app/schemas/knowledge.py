from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import GuidelineStatus, FactStatus


# --- GUIDELINE SCHEMAS ---

class GuidelineCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="general", max_length=100)
    rule_text: str = Field(..., min_length=5)
    prohibited_phrases: Optional[List[str]] = Field(default_factory=list)
    required_phrases: Optional[List[str]] = Field(default_factory=list)
    source: Optional[str] = Field(default="Manual Entry", max_length=255)


class GuidelineUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    rule_text: Optional[str] = Field(None, min_length=5)
    prohibited_phrases: Optional[List[str]] = None
    required_phrases: Optional[List[str]] = None
    source: Optional[str] = None


class GuidelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    title: str
    description: Optional[str] = None
    category: str
    rule_text: str
    prohibited_phrases: Optional[List[str]] = None
    required_phrases: Optional[List[str]] = None
    source: Optional[str] = None
    version: int
    status: GuidelineStatus
    created_by_user_id: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# --- APPROVED FACT SCHEMAS ---

class FactCreateRequest(BaseModel):
    fact_name: str = Field(..., min_length=2, max_length=255)
    approved_value: str = Field(..., min_length=1, max_length=255)
    numeric_value: Optional[float] = None
    numeric_operator: Optional[str] = Field(None, max_length=10)
    unit: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    category: str = Field(default="general", max_length=100)
    source: Optional[str] = Field(default="Manual Entry", max_length=255)
    scope: str = Field(default="global", max_length=255)
    required_qualifiers: Optional[List[str]] = Field(default_factory=list)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class FactUpdateRequest(BaseModel):
    fact_name: Optional[str] = None
    approved_value: Optional[str] = None
    numeric_value: Optional[float] = None
    numeric_operator: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    scope: Optional[str] = None
    required_qualifiers: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class FactSupersedeRequest(BaseModel):
    approved_value: str = Field(..., min_length=1, max_length=255)
    numeric_value: Optional[float] = None
    numeric_operator: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    scope: Optional[str] = None
    required_qualifiers: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class FactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    fact_name: str
    approved_value: str
    numeric_value: Optional[float] = None
    numeric_operator: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    category: str
    source: Optional[str] = None
    scope: str
    required_qualifiers: Optional[List[str]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    version: int
    superseded_by_id: Optional[str] = None
    status: FactStatus
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# --- DOCUMENT IMPORT SCHEMAS ---

class DocumentImportResponse(BaseModel):
    filename: str
    file_type: str
    total_extracted: int
    candidate_guidelines: List[GuidelineResponse]

