"""
Shared internal finding representation for BrandProof Review Engine.

Decoupled from FastAPI request/response lifecycle. Can be serialized into
Pydantic schemas (FindingResponse) or persisted to SQLAlchemy Finding models.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from app.models.enums import FindingVerdict, ReviewLane


@dataclass
class EngineFinding:
    claim_text: str
    verdict: FindingVerdict
    lane: ReviewLane
    explanation: str
    suggested_correction: Optional[str] = None
    fact_id: Optional[str] = None
    fact_name: Optional[str] = None
    fact_version: Optional[int] = None
    fact_approved_value: Optional[str] = None
    guideline_id: Optional[str] = None
    guideline_title: Optional[str] = None
    guideline_version: Optional[int] = None
    confidence_score: Optional[float] = 1.0
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding into a dictionary representation."""
        return {
            "claim_text": self.claim_text,
            "verdict": self.verdict.value if hasattr(self.verdict, "value") else str(self.verdict),
            "lane": self.lane.value if hasattr(self.lane, "value") else str(self.lane),
            "explanation": self.explanation,
            "suggested_correction": self.suggested_correction,
            "fact_id": self.fact_id,
            "fact_name": self.fact_name,
            "fact_version": self.fact_version,
            "fact_approved_value": self.fact_approved_value,
            "guideline_id": self.guideline_id,
            "guideline_title": self.guideline_title,
            "guideline_version": self.guideline_version,
            "confidence_score": self.confidence_score,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
        }
