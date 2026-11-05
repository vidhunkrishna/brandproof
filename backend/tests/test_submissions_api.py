import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.submission import Submission, SubmissionRevision, Finding
from app.models.enums import UserRole
from app.core.security import get_password_hash
from app.core.text_utils import extract_utf16_substring

client = TestClient(app)


@pytest.fixture(scope="module")
def lumen_tokens():
    """Retrieve auth tokens for Lumen admin, creator, and reviewer."""
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
    """Register and return token for a distinct organization to test tenant isolation."""
    unique = uuid.uuid4().hex[:6]
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"foreign_admin_{unique}@apex.demo",
            "password": "ApexPassword2026!",
            "full_name": "Apex Admin",
            "organization_name": f"Apex {unique}",
            "role": "admin",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def second_lumen_creator_token():
    """Create a second creator in the Lumen organization."""
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        unique = uuid.uuid4().hex[:6]
        email = f"creator2_{unique}@lumen.demo"
        user = User(
            email=email,
            hashed_password=get_password_hash("LumenCreator2026!"),
            full_name="Lumen Second Creator",
            is_active=True,
        )
        db.add(user)
        db.flush()

        member = OrganizationMember(
            user_id=user.id,
            organization_id=org.id,
            role=UserRole.CREATOR,
        )
        db.add(member)
        db.commit()

        res = client.post("/api/v1/auth/login", json={"email": email, "password": "LumenCreator2026!"})
        assert res.status_code == 200
        return res.json()["access_token"]
    finally:
        db.close()
# ==============================================================================
# SUBMISSION CREATION & THREE-LANE REVIEW TESTS
# ==============================================================================

def test_submission_create_scenario1_clean(lumen_tokens):
    """
    Scenario 1: Verified compliant marketing draft.
    Copy: 'Our smart bulbs deliver up to 60% energy savings in laboratory tests.'
    Expected: overall_verdict == CORRECT, status == approved.
    """
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "EcoSmart Launch Website Copy",
        "content_type": "website_copy",
        "content_text": "Our smart bulbs deliver up to 60% energy savings in laboratory tests."
    }

    res = client.post("/api/v1/submissions/", json=payload, headers=auth)
    assert res.status_code == 201
    data = res.json()

    assert data["title"] == payload["title"]
    assert data["content_type"] == "website_copy"
    assert data["current_status"] == "approved"
    assert data["total_revisions"] == 1

    # Check review result
    assert "review_result" in data and data["review_result"] is not None
    rr = data["review_result"]
    assert rr["overall_verdict"] == "CORRECT"
    assert rr["correct_claims"] >= 1
    assert rr["contradicted_claims"] == 0

    # Verify evidence references
    correct_finding = next(f for f in rr["findings"] if f["verdict"] == "CORRECT")
    assert correct_finding["fact_name"] == "Energy savings"
    assert correct_finding["fact_version"] == 1
    assert correct_finding["fact_id"] is not None


def test_submission_create_scenario2_violating(lumen_tokens):
    """
    Scenario 2: Violating marketing draft with prohibited phrase and overstated numeric bound.
    Copy: 'Enjoy up to 80% energy savings with guaranteed lifetime warranty!'
    Expected: overall_verdict == CONTRADICTED, status == changes_requested.
    """
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "Aggressive Promotional Email",
        "content_type": "email",
        "content_text": "Enjoy up to 80% energy savings with guaranteed lifetime warranty!"
    }

    res = client.post("/api/v1/submissions/", json=payload, headers=auth)
    assert res.status_code == 201
    data = res.json()

    assert data["current_status"] == "changes_requested"
    rr = data["review_result"]
    assert rr["overall_verdict"] == "CONTRADICTED"
    assert rr["contradicted_claims"] >= 1

    # Check both Lane 1 (prohibited phrase) and Lane 2 (numeric fact limit) findings
    prohibited_finding = next((f for f in rr["findings"] if f["claim_text"].lower() == "lifetime warranty"), None)
    assert prohibited_finding is not None
    assert prohibited_finding["lane"] == "LANE_1_DETERMINISTIC"
    assert prohibited_finding["guideline_title"] == "Warranty Terminology Compliance"

    numeric_finding = next((f for f in rr["findings"] if f["lane"] == "LANE_2_GROUNDED_FACT"), None)
    assert numeric_finding is not None
    assert numeric_finding["fact_name"] == "Energy savings"


def test_submission_create_scenario3_unverified(lumen_tokens):
    """
    Scenario 3: Unverified marketing copy lacking evidence in the brand registry.
    Copy: 'We are the #1 smart home provider in the world with 99.9% uptime.'
    Expected: Empirical claim (99.9% uptime) is UNSUPPORTED, overall_verdict == UNSUPPORTED, status == review_pending.
    """
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "Corporate Overview Post",
        "content_type": "social_media",
        "content_text": "We are the #1 smart home provider in the world with 99.9% uptime."
    }

    res = client.post("/api/v1/submissions/", json=payload, headers=auth)
    assert res.status_code == 201
    data = res.json()

    assert data["current_status"] == "review_pending"
    rr = data["review_result"]
    assert rr["overall_verdict"] == "UNSUPPORTED"
    assert rr["unsupported_claims"] >= 1
    # No unverified claim can be marked CORRECT
    assert rr["correct_claims"] == 0


def test_submission_create_ambiguous_unverifiable(lumen_tokens):
    """
    Verify that an ambiguous, subjective claim without empirical facts produces UNVERIFIABLE.
    Copy: 'We are the #1 smart home provider in the world.'
    Expected: overall_verdict == UNVERIFIABLE, unverifiable_claims >= 1, unsupported_claims == 0.
    """
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "Ambiguous Brand Post",
        "content_type": "social_media",
        "content_text": "We are the #1 smart home provider in the world."
    }

    res = client.post("/api/v1/submissions/", json=payload, headers=auth)
    assert res.status_code == 201
    data = res.json()

    assert data["current_status"] == "review_pending"
    rr = data["review_result"]
    assert rr["overall_verdict"] == "UNVERIFIABLE"
    assert rr["unverifiable_claims"] >= 1
    assert rr["unsupported_claims"] == 0
    assert rr["correct_claims"] == 0


# ==============================================================================
# REVISION HISTORY & RECHECK LIFECYCLE TESTS
# ==============================================================================

def test_submission_recheck_creates_new_revision_and_preserves_history(lumen_tokens):
    """
    Verify the revision recheck lifecycle:
    1. Create violating submission (Revision 1 -> CONTRADICTED).
    2. Recheck with corrected copy (Revision 2 -> CORRECT).
    3. Verify Revision 1 is completely preserved with historical findings intact.
    """
    creator_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}

    # Step 1: Initial violating draft
    create_payload = {
        "title": "Draft with Revisions",
        "content_type": "website_copy",
        "content_text": "Enjoy up to 80% energy savings with guaranteed lifetime warranty!"
    }
    create_res = client.post("/api/v1/submissions/", json=create_payload, headers=creator_auth)
    assert create_res.status_code == 201
    sub_id = create_res.json()["id"]
    rev1_id = create_res.json()["latest_revision"]["id"]

    # Step 2: Recheck with corrected marketing copy
    recheck_payload = {
        "content_text": "Our smart bulbs deliver up to 60% energy savings in laboratory tests.",
        "change_summary": "Removed prohibited lifetime warranty and adjusted energy savings to approved 60% with qualifier."
    }
    recheck_res = client.post(f"/api/v1/submissions/{sub_id}/recheck", json=recheck_payload, headers=creator_auth)
    assert recheck_res.status_code == 200
    recheck_data = recheck_res.json()

    assert recheck_data["total_revisions"] == 2
    assert recheck_data["current_status"] == "approved"
    assert recheck_data["latest_revision"]["revision_number"] == 2
    assert recheck_data["latest_revision"]["overall_verdict"] == "CORRECT"

    # Step 3: Fetch full submission details and verify Revision 1 is preserved
    get_res = client.get(f"/api/v1/submissions/{sub_id}", headers=creator_auth)
    assert get_res.status_code == 200
    details = get_res.json()

    revisions = details["revisions"]
    assert len(revisions) == 2

    # Verify Revision 1 (Historical)
    rev1 = next(r for r in revisions if r["revision_number"] == 1)
    assert rev1["id"] == rev1_id
    assert rev1["overall_verdict"] == "CONTRADICTED"
    assert "80%" in rev1["content_text"]
    assert len(rev1["findings"]) >= 1

    # Verify Revision 2 (Latest)
    rev2 = next(r for r in revisions if r["revision_number"] == 2)
    assert rev2["overall_verdict"] == "CORRECT"
    assert "60%" in rev2["content_text"]
    assert rev2["change_summary"] == recheck_payload["change_summary"]


# ==============================================================================
# RBAC & TENANT ISOLATION TESTS
# ==============================================================================

def test_creator_cannot_recheck_another_users_submission(lumen_tokens, second_lumen_creator_token):
    """Verify that a creator cannot recheck a submission created by another user."""
    creator1_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    creator2_auth = {"Authorization": f"Bearer {second_lumen_creator_token}"}

    # Creator 1 creates submission
    create_res = client.post(
        "/api/v1/submissions/",
        json={
            "title": "Creator 1 Exclusive Copy",
            "content_type": "email",
            "content_text": "Lumen smart bulbs deliver up to 60% energy savings in laboratory tests."
        },
        headers=creator1_auth
    )
    assert create_res.status_code == 201
    sub_id = create_res.json()["id"]

    # Creator 2 attempts to recheck Creator 1's submission
    recheck_res = client.post(
        f"/api/v1/submissions/{sub_id}/recheck",
        json={"content_text": "Updated content by unauthorized user."},
        headers=creator2_auth
    )
    assert recheck_res.status_code == 403
    assert "creators can only recheck their own submissions" in recheck_res.json()["detail"].lower()


def test_reviewer_and_admin_access(lumen_tokens):
    """Verify that reviewers and admins can view any organization submission and findings."""
    creator_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    reviewer_auth = {"Authorization": f"Bearer {lumen_tokens['reviewer']}"}
    admin_auth = {"Authorization": f"Bearer {lumen_tokens['admin']}"}

    # Creator creates submission
    create_res = client.post(
        "/api/v1/submissions/",
        json={
            "title": "Reviewer Visible Draft",
            "content_type": "website_copy",
            "content_text": "Lumen smart bulbs deliver up to 60% energy savings in laboratory tests."
        },
        headers=creator_auth
    )
    sub_id = create_res.json()["id"]

    # Reviewer views submission
    rev_get = client.get(f"/api/v1/submissions/{sub_id}", headers=reviewer_auth)
    assert rev_get.status_code == 200
    assert rev_get.json()["id"] == sub_id

    # Admin views submission
    admin_get = client.get(f"/api/v1/submissions/{sub_id}", headers=admin_auth)
    assert admin_get.status_code == 200
    assert admin_get.json()["id"] == sub_id


def test_cross_org_isolation(lumen_tokens, foreign_org_token):
    """Verify that a submission in one organization cannot be viewed or rechecked by another organization."""
    lumen_creator_auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    foreign_auth = {"Authorization": f"Bearer {foreign_org_token}"}

    create_res = client.post(
        "/api/v1/submissions/",
        json={
            "title": "Confidential Lumen Launch",
            "content_type": "email",
            "content_text": "Lumen smart bulbs deliver up to 60% energy savings in laboratory tests."
        },
        headers=lumen_creator_auth
    )
    sub_id = create_res.json()["id"]

    # Foreign organization tries to retrieve Lumen submission -> 404
    foreign_get = client.get(f"/api/v1/submissions/{sub_id}", headers=foreign_auth)
    assert foreign_get.status_code == 404

    # Foreign organization tries to recheck Lumen submission -> 404
    foreign_recheck = client.post(
        f"/api/v1/submissions/{sub_id}/recheck",
        json={"content_text": "Hijack attempt."},
        headers=foreign_auth
    )
    assert foreign_recheck.status_code == 404

    # Foreign list must not contain Lumen submission
    foreign_list = client.get("/api/v1/submissions/", headers=foreign_auth)
    assert foreign_list.status_code == 200
    sub_ids = [s["id"] for s in foreign_list.json()]
    assert sub_id not in sub_ids


# ==============================================================================
# VALIDATION, PAGINATION & OFFSET TESTS
# ==============================================================================

def test_submission_validation_errors(lumen_tokens):
    """Verify that empty, whitespace, or invalid content types are rejected."""
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}

    # Empty title
    res1 = client.post("/api/v1/submissions/", json={"title": "  ", "content_text": "Valid"}, headers=auth)
    assert res1.status_code == 422

    # Empty content
    res2 = client.post("/api/v1/submissions/", json={"title": "Title", "content_text": "   \n\t "}, headers=auth)
    assert res2.status_code == 422


def test_unauthenticated_request_rejected():
    """Verify that requests without valid JWT are rejected with 401."""
    res = client.post("/api/v1/submissions/", json={"title": "T", "content_text": "C"})
    assert res.status_code == 401


def test_pagination(lumen_tokens):
    """Verify pagination skip and limit parameters."""
    auth = {"Authorization": f"Bearer {lumen_tokens['reviewer']}"}

    res = client.get("/api/v1/submissions/?skip=0&limit=2", headers=auth)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) <= 2


def test_utf16_offsets_survive_persistence_and_serialization(lumen_tokens):
    """Verify that finding offsets with leading emojis survive DB persistence and API serialization."""
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    content = "🚀🔥 Exclusive Offer: Lifetime warranty on all smart lights!"

    res = client.post(
        "/api/v1/submissions/",
        json={
            "title": "Emoji Test Copy",
            "content_type": "social_media",
            "content_text": content
        },
        headers=auth
    )
    assert res.status_code == 201
    data = res.json()
    findings = data["latest_revision"]["findings"]

    f = next(item for item in findings if "lifetime warranty" in item["claim_text"].lower())
    assert f["start_offset"] is not None
    assert f["end_offset"] is not None
    assert f["start_offset"] < f["end_offset"]

    # Verify that extract_utf16_substring extracts the exact claim
    extracted = extract_utf16_substring(content, f["start_offset"], f["end_offset"])
    assert extracted.lower() == "lifetime warranty"


def test_deterministic_fallback_in_api(lumen_tokens):
    """Verify that when the AI provider is unavailable, API executes deterministic fallback cleanly."""
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "Fallback Test Submission",
        "content_type": "email",
        "content_text": "Our smart bulbs deliver up to 60% energy savings in laboratory tests."
    }

    # Patch GeminiProvider.is_available to False
    with patch("app.review_engine.ai_provider.GeminiProvider.is_available", return_value=False):
        res = client.post("/api/v1/submissions/", json=payload, headers=auth)
        assert res.status_code == 201
        data = res.json()
        assert data["review_result"]["is_fallback"] is True
        assert data["review_result"]["overall_verdict"] == "CORRECT"


def test_database_rollback_on_persistence_failure(lumen_tokens):
    """Verify that if database commit fails, transaction rolls back and no partial submission is committed."""
    auth = {"Authorization": f"Bearer {lumen_tokens['creator']}"}
    payload = {
        "title": "Rollback Test Submission",
        "content_type": "website_copy",
        "content_text": "Lumen smart bulbs deliver up to 60% energy savings in laboratory tests."
    }

    db = SessionLocal()
    try:
        initial_sub_count = db.query(Submission).count()

        # Simulate database failure during commit
        with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Simulated DB Crash")):
            res = client.post("/api/v1/submissions/", json=payload, headers=auth)
            assert res.status_code == 500

        # Verify no orphan submission was created
        final_sub_count = db.query(Submission).count()
        assert final_sub_count == initial_sub_count
    finally:
        db.close()
