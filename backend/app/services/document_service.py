from typing import List
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.api.deps import TenantContext
from app.models.knowledge import Guideline
from app.models.enums import GuidelineStatus
from app.document_processing.parser import DocumentParser
from app.schemas.knowledge import DocumentImportResponse, GuidelineResponse


class DocumentService:
    @staticmethod
    async def import_document(
        db: Session,
        ctx: TenantContext,
        file: UploadFile
    ) -> DocumentImportResponse:
        ext = DocumentParser.validate_file(file)
        file_bytes = await file.read()
        full_text = DocumentParser.extract_text(file_bytes, ext)
        raw_candidates = DocumentParser.extract_candidate_rules(full_text, file.filename or "Uploaded Document")

        saved_candidates = []
        for c in raw_candidates:
            # Staged in DRAFT status requiring explicit admin approval
            guideline = Guideline(
                organization_id=ctx.org_id,
                title=c["title"],
                description=f"Auto-extracted rule candidate from document: {file.filename}",
                category=c["category"],
                rule_text=c["rule_text"],
                prohibited_phrases=c["prohibited_phrases"],
                required_phrases=c["required_phrases"],
                source=c["source"],
                version=1,
                status=GuidelineStatus.DRAFT,
                created_by_user_id=ctx.user.id,
                approved_by_user_id=None,
                approved_at=None
            )
            db.add(guideline)
            saved_candidates.append(guideline)

        db.commit()
        for g in saved_candidates:
            db.refresh(g)

        return DocumentImportResponse(
            filename=file.filename or "unknown",
            file_type=ext.lstrip("."),
            total_extracted=len(saved_candidates),
            candidate_guidelines=[GuidelineResponse.model_validate(g) for g in saved_candidates]
        )

