from io import BytesIO
from fastapi import APIRouter, Depends, UploadFile, File, Response, status
from sqlalchemy.orm import Session
from docx import Document
from app.core.database import get_db
from app.api.deps import get_tenant_context, TenantContext
from app.schemas.knowledge import DocumentImportResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Document Processing"])


@router.get("/sample-file")
def get_sample_document():
    """Download or load a pre-packaged sample Lumen Brand Guidelines document (.docx)
    ready for automated candidate rule extraction.
    """
    doc = Document()
    doc.add_heading("Lumen Smart Lighting — Brand Guidelines & Policy Manual 2026", level=1)
    doc.add_paragraph(
        "This sample policy document contains brand governance rules designed to test the BrandProof "
        "candidate rule extraction engine."
    )

    doc.add_heading("Section 1: Energy & Performance Claims", level=2)
    doc.add_paragraph(
        'Marketing copy must state energy savings up to 60% and must include the qualifier "in laboratory tests". '
        'Never claim "80% energy savings" or unconditional power reductions.'
    )

    doc.add_heading("Section 2: Warranty & Customer Guarantee", level=2)
    doc.add_paragraph(
        'Product warranty is strictly 3 years. Marketing copy must never promise a "lifetime warranty" '
        'or "unconditional lifetime replacement".'
    )

    doc.add_heading("Section 3: Durability & Lifespan Standards", level=2)
    doc.add_paragraph(
        'All lifespan claims must specify 25,000 hours and note "under standard residential usage". '
        'Never claim "bulbs that never burn out" or infinite lifespan.'
    )

    doc.add_heading("Section 4: Wireless & Connectivity Certifications", level=2)
    doc.add_paragraph(
        'Marketing materials must only state compatibility with certified standards (Matter, Apple HomeKit, Google Home). '
        'Claims of "universal wireless compatibility" are strictly prohibited.'
    )

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=Lumen_Brand_Guidelines_Sample.docx"
        }
    )


@router.post("/import", response_model=DocumentImportResponse, status_code=status.HTTP_201_CREATED)

async def import_document(
    file: UploadFile = File(..., description="Text-based PDF or Microsoft Word (.docx) brand book"),
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Upload a brand guidelines document (PDF or DOCX).
    Extracts text, identifies policy/governance rules, and stages them as candidate guidelines in DRAFT status.
    """
    return await DocumentService.import_document(db, ctx, file)

