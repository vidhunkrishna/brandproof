import io
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfWriter
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def lumen_tokens():
    """Retrieves authentication tokens for Lumen admin, creator, and reviewer."""
    tokens = {}
    for role, email, pwd in [
        ("admin", "admin@lumen.demo", "LumenAdmin2026!"),
        ("creator", "creator@lumen.demo", "LumenCreator2026!"),
        ("reviewer", "reviewer@lumen.demo", "LumenReviewer2026!"),
    ]:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        assert res.status_code == 200, f"Login failed for {email}"
        tokens[role] = res.json()["access_token"]
    return tokens


@pytest.fixture(scope="module")
def foreign_org_token():
    """Registers and returns token for a separate organization to test tenant isolation."""
    unique = uuid.uuid4().hex[:6]
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner_{unique}@nebula.demo",
            "password": "NebulaPassword2026!",
            "full_name": "Nebula Admin",
            "organization_name": f"Nebula {unique}",
            "role": "admin"
        }
    )
    assert res.status_code == 201
    return res.json()["access_token"]


# --- GUIDELINE TESTS ---

def test_guideline_crud_and_versioning(lumen_tokens):
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # 1. Create Guideline
    create_payload = {
        "title": "Pricing Transparency Standard",
        "category": "pricing",
        "rule_text": "All promotional pricing must include applicable taxes and must not hide recurring subscription fees.",
        "prohibited_phrases": ["hidden fee", "surprise charges"],
        "required_phrases": ["taxes included"],
        "source": "Brand Governance Playbook 2026"
    }
    create_res = client.post("/api/v1/guidelines/", json=create_payload, headers=admin_auth)
    assert create_res.status_code == 201
    g_data = create_res.json()
    assert g_data["version"] == 1
    assert g_data["status"] == "active"  # Admin-created guidelines are active
    g_id = g_data["id"]

    # 2. Get Guideline
    get_res = client.get(f"/api/v1/guidelines/{g_id}", headers=admin_auth)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Pricing Transparency Standard"

    # 3. Update Guideline with rule change -> Bumps version
    update_payload = {
        "rule_text": "All promotional pricing must include applicable taxes, shipping estimates, and recurring subscription fees.",
        "required_phrases": ["taxes included", "shipping included"]
    }
    update_res = client.put(f"/api/v1/guidelines/{g_id}", json=update_payload, headers=admin_auth)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["version"] == 2
    assert "shipping included" in updated_data["required_phrases"]

    # 4. List Guidelines with filter
    list_res = client.get("/api/v1/guidelines/?category=pricing", headers=admin_auth)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Archive Guideline
    del_res = client.delete(f"/api/v1/guidelines/{g_id}", headers=admin_auth)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "archived"


def test_guideline_creator_approval_workflow(lumen_tokens):
    creator_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # 1. Creator creates a guideline -> Staged as DRAFT
    create_res = client.post(
        "/api/v1/guidelines/",
        json={
            "title": "Creator Proposed Social Media Policy",
            "category": "social",
            "rule_text": "Social media posts must always tag verified company partners.",
            "source": "Creator Proposal"
        },
        headers=creator_auth
    )
    assert create_res.status_code == 201
    draft_g = create_res.json()
    assert draft_g["status"] == "draft"
    assert draft_g["approved_at"] is None
    g_id = draft_g["id"]

    # 2. Creator attempts to approve -> Must receive 403 Forbidden
    creator_approve_res = client.put(f"/api/v1/guidelines/{g_id}/approve", headers=creator_auth)
    assert creator_approve_res.status_code == 403
    assert "Only Organization Admins" in creator_approve_res.json()["detail"]

    # 3. Admin approves -> Status becomes ACTIVE with timestamp
    admin_approve_res = client.put(f"/api/v1/guidelines/{g_id}/approve", headers=admin_auth)
    assert admin_approve_res.status_code == 200
    active_g = admin_approve_res.json()
    assert active_g["status"] == "active"
    assert active_g["approved_at"] is not None
    assert active_g["approved_by_user_id"] is not None


# --- APPROVED FACT TESTS ---

def test_approved_fact_crud_and_supersede(lumen_tokens):
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # 1. Create initial Fact v1
    fact_payload = {
        "fact_name": "Battery Life",
        "approved_value": "Up to 24 hours of continuous playback",
        "numeric_value": 24.0,
        "numeric_operator": "<=",
        "unit": "hours",
        "description": "Standard audio playback test result.",
        "category": "performance",
        "scope": "consumer audio",
        "required_qualifiers": ["continuous playback"],
        "source": "Battery Lab Report 2025"
    }
    create_res = client.post("/api/v1/facts/", json=fact_payload, headers=admin_auth)
    assert create_res.status_code == 201
    v1_fact = create_res.json()
    assert v1_fact["version"] == 1
    assert v1_fact["status"] == "approved"
    v1_id = v1_fact["id"]

    # 2. Supersede Fact with v2 (New lab results: 30 hours)
    supersede_payload = {
        "approved_value": "Up to 30 hours of continuous playback with firmware 2.0",
        "numeric_value": 30.0,
        "numeric_operator": "<=",
        "unit": "hours",
        "description": "Updated battery performance under Firmware 2.0.",
        "source": "Battery Lab Report 2026-Q1"
    }
    supersede_res = client.post(f"/api/v1/facts/{v1_id}/supersede", json=supersede_payload, headers=admin_auth)
    assert supersede_res.status_code == 201
    v2_fact = supersede_res.json()
    assert v2_fact["version"] == 2
    assert v2_fact["status"] == "approved"
    assert v2_fact["approved_value"] == "Up to 30 hours of continuous playback with firmware 2.0"
    v2_id = v2_fact["id"]

    # 3. Verify v1 is marked SUPERSEDED and points to v2
    v1_check = client.get(f"/api/v1/facts/{v1_id}", headers=admin_auth).json()
    assert v1_check["status"] == "superseded"
    assert v1_check["superseded_by_id"] == v2_id


def test_fact_creator_permission_restrictions(lumen_tokens):
    creator_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}

    # 1. Creator creates fact -> Staged as PENDING_APPROVAL
    create_res = client.post(
        "/api/v1/facts/",
        json={
            "fact_name": "Proposed Fast Charging",
            "approved_value": "50% charge in 15 minutes",
            "category": "performance"
        },
        headers=creator_auth
    )
    assert create_res.status_code == 201
    fact_id = create_res.json()["id"]
    assert create_res.json()["status"] == "pending_approval"

    # 2. Creator attempts to approve -> 403 Forbidden
    approve_res = client.put(f"/api/v1/facts/{fact_id}/approve", headers=creator_auth)
    assert approve_res.status_code == 403

    # 3. Creator attempts to supersede -> 403 Forbidden
    supersede_res = client.post(
        f"/api/v1/facts/{fact_id}/supersede",
        json={"approved_value": "New Value"},
        headers=creator_auth
    )
    assert supersede_res.status_code == 403


# --- DOCUMENT IMPORT TESTS ---

def test_document_import_docx(lumen_tokens):
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # Create synthetic DOCX in memory
    doc = Document()
    doc.add_heading("Lumen Brand Voice and Performance Guidelines", 0)
    doc.add_paragraph("Marketing claims must always reflect certified lab testing.")
    doc.add_paragraph("Prohibited terms: You must never claim 'unlimited battery' or 'eternal lifespan'.")
    doc.add_paragraph("Warranty coverage is required to specify 3 years for consumer units.")
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)

    res = client.post(
        "/api/v1/documents/import",
        files={"file": ("BrandBook2026.docx", doc_io, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=admin_auth
    )
    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "BrandBook2026.docx"
    assert data["total_extracted"] >= 2
    for candidate in data["candidate_guidelines"]:
        assert candidate["status"] == "draft"
        assert candidate["source"] == "BrandBook2026.docx"


def test_document_import_invalid_file_type(lumen_tokens):
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}
    fake_txt = io.BytesIO(b"Some text")
    res = client.post(
        "/api/v1/documents/import",
        files={"file": ("malicious.exe", fake_txt, "application/x-msdownload")},
        headers=admin_auth
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


# --- CROSS-ORGANIZATION TENANT ISOLATION TESTS ---

def test_cross_org_guidelines_and_facts_isolation(lumen_tokens, foreign_org_token):
    lumen_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}
    foreign_auth = {"Authorization": f"Bearer {foreign_org_token}"}

    # 1. Create Guideline in Lumen
    lumen_g = client.post(
        "/api/v1/guidelines/",
        json={"title": "Lumen Secret Guideline", "rule_text": "Lumen internal policy must be respected."},
        headers=lumen_auth
    ).json()

    # 2. Foreign Org attempts to GET Lumen's guideline -> 404 Not Found
    foreign_get_g = client.get(f"/api/v1/guidelines/{lumen_g['id']}", headers=foreign_auth)
    assert foreign_get_g.status_code == 404

    # 3. Foreign Org attempts to UPDATE Lumen's guideline -> 404 Not Found
    foreign_put_g = client.put(
        f"/api/v1/guidelines/{lumen_g['id']}",
        json={"title": "Hacked Title"},
        headers=foreign_auth
    )
    assert foreign_put_g.status_code == 404

    # 4. Foreign Org listing guidelines sees 0 Lumen guidelines
    foreign_list_g = client.get("/api/v1/guidelines/", headers=foreign_auth).json()
    assert all(g["id"] != lumen_g["id"] for g in foreign_list_g)

    # 5. Create Fact in Lumen
    lumen_f = client.post(
        "/api/v1/facts/",
        json={"fact_name": "Lumen Proprietary Spec", "approved_value": "99.9% uptime"},
        headers=lumen_auth
    ).json()

    # 6. Foreign Org attempts to GET Lumen's fact -> 404 Not Found
    foreign_get_f = client.get(f"/api/v1/facts/{lumen_f['id']}", headers=foreign_auth)
    assert foreign_get_f.status_code == 404

    # 7. Foreign Org attempts to SUPERSEDE Lumen's fact -> 404 Not Found
    foreign_supersede_f = client.post(
        f"/api/v1/facts/{lumen_f['id']}/supersede",
        json={"approved_value": "Compromised Uptime"},
        headers=foreign_auth
    )
    assert foreign_supersede_f.status_code == 404



# --- ADDITIONAL VERIFICATION TESTS ---

def test_approved_items_contain_approval_metadata(lumen_tokens):
    """Verify that every approved fact and active guideline contains valid approval metadata."""
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}
    
    # 1. Guidelines
    guidelines_res = client.get("/api/v1/guidelines/?status=active", headers=admin_auth)
    assert guidelines_res.status_code == 200
    guidelines = guidelines_res.json()
    assert len(guidelines) >= 2
    for g in guidelines:
        assert g["approved_by_user_id"] is not None, f"Guideline {g['id']} missing approved_by_user_id"
        assert g["approved_at"] is not None, f"Guideline {g['id']} missing approved_at"

    # 2. Approved Facts
    facts_res = client.get("/api/v1/facts/?status=approved", headers=admin_auth)
    assert facts_res.status_code == 200
    facts = facts_res.json()
    assert len(facts) >= 2
    for f in facts:
        assert f["approved_by_user_id"] is not None, f"Fact {f['id']} missing approved_by_user_id"
        assert f["approved_at"] is not None, f"Fact {f['id']} missing approved_at"


def test_historical_submission_reference_retention(lumen_tokens):
    """Verify that historical findings retain references to original fact versions even after superseding."""
    from app.core.database import SessionLocal
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.submission import Submission, SubmissionRevision, Finding
    from app.models.enums import FindingVerdict, ReviewLane
    
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # 1. Create a fact v1
    create_res = client.post(
        "/api/v1/facts/",
        json={"fact_name": "Screen Refresh Rate", "approved_value": "120Hz ProMotion", "numeric_value": 120.0},
        headers=admin_auth
    )
    v1_id = create_res.json()["id"]

    # 2. Simulate a historical submission and finding linked to v1
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        user = db.query(User).filter(User.email == "creator@lumen.demo").first()
        
        submission = Submission(
            organization_id=org.id,
            creator_user_id=user.id,
            title="Q1 Display Promo"
        )
        db.add(submission)
        db.flush()

        revision = SubmissionRevision(
            submission_id=submission.id,
            revision_number=1,
            content_text="Our screen operates at 120Hz."
        )
        db.add(revision)
        db.flush()

        finding = Finding(
            submission_revision_id=revision.id,
            claim_text="120Hz",
            verdict=FindingVerdict.CORRECT,
            lane=ReviewLane.LANE_2_GROUNDED_FACT,
            explanation="Matches approved display specification v1.",
            fact_id=v1_id
        )
        db.add(finding)
        db.commit()
        finding_id = finding.id
    finally:
        db.close()

    # 3. Now supersede v1 to v2 (upgrade to 144Hz)
    supersede_res = client.post(
        f"/api/v1/facts/{v1_id}/supersede",
        json={"approved_value": "144Hz ProMotion Gaming", "numeric_value": 144.0, "source": "Display Spec 2026"},
        headers=admin_auth
    )
    assert supersede_res.status_code == 201
    v2_id = supersede_res.json()["id"]

    # 4. Verify historical finding STILL references v1, and v1 accurately points to v2
    db = SessionLocal()
    try:
        retrieved_finding = db.query(Finding).filter(Finding.id == finding_id).first()
        assert retrieved_finding is not None
        assert retrieved_finding.fact_id == v1_id  # Historical link preserved!
        assert retrieved_finding.fact.status.value == "superseded"
        assert retrieved_finding.fact.superseded_by_id == v2_id
    finally:
        db.close()


def test_document_import_oversized_file(lumen_tokens):
    """Verify that uploading a file exceeding 10MB limit is rejected with 400 Bad Request."""
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}
    oversized_data = b"0" * (10 * 1024 * 1024 + 1024)  # 10MB + 1KB
    res = client.post(
        "/api/v1/documents/import",
        files={"file": ("oversized.pdf", io.BytesIO(oversized_data), "application/pdf")},
        headers=admin_auth
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed size" in res.json()["detail"]


def test_document_import_unextractable_empty_pdf(lumen_tokens):
    """Verify that uploading an empty PDF with no extractable text returns 422 Unprocessable Entity."""
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}
    empty_writer = PdfWriter()
    empty_writer.add_blank_page(width=100, height=100)
    pdf_io = io.BytesIO()
    empty_writer.write(pdf_io)
    pdf_io.seek(0)

    res = client.post(
        "/api/v1/documents/import",
        files={"file": ("blank.pdf", pdf_io, "application/pdf")},
        headers=admin_auth
    )
    assert res.status_code == 422
    assert "No extractable text found" in res.json()["detail"]


def test_document_sample_file_download():
    """Verify that GET /api/v1/documents/sample-file delivers a valid Word .docx sample."""
    res = client.get("/api/v1/documents/sample-file")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in res.headers["content-type"]
    assert "Lumen_Brand_Guidelines_Sample.docx" in res.headers.get("content-disposition", "")
    assert len(res.content) > 1000
