import pytest
import uuid
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.core.config import Settings
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.knowledge import ApprovedFact, Guideline
from app.models.enums import UserRole

client = TestClient(app)


def test_health_check():
    """Verify health endpoint reports healthy and database connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"


def test_jwt_production_validation():
    """Verify that in production mode, an insecure or default SECRET_KEY raises a validation error."""
    import os
    orig_env = os.environ.get("ENVIRONMENT")
    try:
        os.environ["ENVIRONMENT"] = "production"
        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="brandproof-hackathon-insecure-default-key-change-in-production"
            )
    finally:
        if orig_env is not None:
            os.environ["ENVIRONMENT"] = orig_env
        else:
            os.environ.pop("ENVIRONMENT", None)


def test_demo_user_login_success():
    """Verify seeded demo admin, creator, and reviewer accounts can authenticate."""
    for email, pwd, expected_role in [
        ("admin@lumen.demo", "LumenAdmin2026!", "admin"),
        ("creator@lumen.demo", "LumenCreator2026!", "creator"),
        ("reviewer@lumen.demo", "LumenReviewer2026!", "reviewer"),
    ]:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": pwd}
        )
        assert response.status_code == 200, f"Failed to login with {email}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert data["active_organization"]["name"] == "Lumen"
        assert data["role"] == expected_role


def test_login_invalid_password():
    """Verify 401 is returned when an invalid password is provided."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@lumen.demo", "password": "WrongPassword999!"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_duplicate_email_registration_fails():
    """Verify that registering an already existing email returns 400 Bad Request."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@lumen.demo",
            "password": "SomeNewPassword123!",
            "full_name": "Imposter Admin",
            "organization_name": "Lumen",
            "role": "admin"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_passwords_never_returned_in_api_responses():
    """Verify that neither plain password nor hashed_password appear in any API response."""
    # 1. Test in Login Response
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@lumen.demo", "password": "LumenCreator2026!"}
    )
    login_data = login_res.json()
    assert "password" not in login_data["user"]
    assert "hashed_password" not in login_data["user"]

    token = login_data["access_token"]

    # 2. Test in /auth/me Response
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    me_data = me_res.json()
    assert "password" not in me_data["user"]
    assert "hashed_password" not in me_data["user"]

    # 3. Test in Register Response
    unique_email = f"audit_{uuid.uuid4().hex[:6]}@lumen.demo"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "SecurePassword2026!",
            "full_name": "Audit User",
            "organization_name": "Audit Org",
            "role": "creator"
        }
    )
    reg_data = reg_res.json()
    assert "password" not in reg_data["user"]
    assert "hashed_password" not in reg_data["user"]


def test_organisation_membership_uniqueness_constraint():
    """Verify database unique constraint (uq_org_user) prevents duplicate memberships for same org and user."""
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        user = db.query(User).filter(User.email == "admin@lumen.demo").first()
        assert org is not None and user is not None

        # Attempt to insert an identical membership record
        duplicate_membership = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=UserRole.ADMIN
        )
        db.add(duplicate_membership)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_auth_me_profile_retrieval():
    """Verify /auth/me returns the user profile, active organization, and verified role."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@lumen.demo", "password": "LumenCreator2026!"}
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["user"]["email"] == "creator@lumen.demo"
    assert profile["role"] == "creator"
    assert profile["active_organization"]["slug"] == "lumen"
    assert len(profile["memberships"]) >= 1


def test_rbac_admin_endpoint_enforcement():
    """Verify RBAC: Admin succeeds, whereas Creator and Reviewer receive 403 Forbidden."""
    # 1. Login as Admin -> Should succeed
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@lumen.demo", "password": "LumenAdmin2026!"}
    ).json()
    admin_res = client.get(
        "/api/v1/auth/admin-only-check",
        headers={"Authorization": f"Bearer {admin_login['access_token']}"}
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["status"] == "authorized"

    # 2. Login as Creator -> Must fail with 403
    creator_login = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@lumen.demo", "password": "LumenCreator2026!"}
    ).json()
    creator_res = client.get(
        "/api/v1/auth/admin-only-check",
        headers={"Authorization": f"Bearer {creator_login['access_token']}"}
    )
    assert creator_res.status_code == 403
    assert "Operation requires one of the following roles: [admin]" in creator_res.json()["detail"]

    # 3. Login as Reviewer -> Must fail with 403
    reviewer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@lumen.demo", "password": "LumenReviewer2026!"}
    ).json()
    reviewer_res = client.get(
        "/api/v1/auth/admin-only-check",
        headers={"Authorization": f"Bearer {reviewer_login['access_token']}"}
    )
    assert reviewer_res.status_code == 403


def test_invalid_or_expired_jwt():
    """Verify that an expired token or invalid signature is rejected with 401."""
    expired_token = create_access_token(
        {"sub": "non-existent-user", "org_id": "none", "role": "admin"},
        expires_delta=timedelta(seconds=-10)
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert res.status_code == 401

    res_garbage = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this-is-not-a-valid-jwt-token"}
    )
    assert res_garbage.status_code == 401


def test_user_registration_and_organisation_isolation():
    """Verify new organization registration and tenant isolation between distinct orgs."""
    unique_suffix = str(uuid.uuid4())[:8]
    org_name = f"Nova Corp {unique_suffix}"
    email = f"lead_{unique_suffix}@nova.demo"

    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "NovaPassword2026!",
            "full_name": "Nova Lead",
            "organization_name": org_name,
            "role": "admin"
        }
    )
    assert reg_res.status_code == 201
    nova_data = reg_res.json()
    nova_token = nova_data["access_token"]
    nova_org_id = nova_data["active_organization"]["id"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {nova_token}"}
    )
    assert me_res.status_code == 200
    nova_profile = me_res.json()
    assert nova_profile["active_organization"]["name"] == org_name
    assert nova_profile["role"] == "admin"

    lumen_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@lumen.demo", "password": "LumenAdmin2026!"}
    ).json()
    lumen_org_id = lumen_login["active_organization"]["id"]
    assert nova_org_id != lumen_org_id

    # Cross-org forged token fails:
    forged_token = create_access_token({
        "sub": nova_data["user"]["id"],
        "email": email,
        "org_id": lumen_org_id,
        "role": "admin"
    })
    forged_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"}
    )
    assert forged_res.status_code == 403
    assert "user is not a member of this organization" in forged_res.json()["detail"]


def test_database_persistence_and_cross_org_query_isolation():
    """Verify that database queries partitioned by organization_id guarantee zero tenant leakage."""
    db = SessionLocal()
    try:
        lumen_org = db.query(Organization).filter(Organization.slug == "lumen").first()
        assert lumen_org is not None

        # Create a second dummy tenant organization
        dummy_org = Organization(name="Isolated Org", slug=f"isolated-{uuid.uuid4().hex[:6]}")
        db.add(dummy_org)
        db.commit()
        db.refresh(dummy_org)

        # 1. Facts Query Isolation
        lumen_facts = db.query(ApprovedFact).filter(ApprovedFact.organization_id == lumen_org.id).all()
        dummy_facts = db.query(ApprovedFact).filter(ApprovedFact.organization_id == dummy_org.id).all()
        assert len(lumen_facts) >= 2
        assert len(dummy_facts) == 0  # Tenant 2 sees none of Lumen's facts

        # 2. Guidelines Query Isolation
        lumen_guidelines = db.query(Guideline).filter(Guideline.organization_id == lumen_org.id).all()
        dummy_guidelines = db.query(Guideline).filter(Guideline.organization_id == dummy_org.id).all()
        assert len(lumen_guidelines) >= 2
        assert len(dummy_guidelines) == 0  # Tenant 2 sees none of Lumen's guidelines

        # Verify Lumen facts content
        fact_names = {f.fact_name: f.approved_value for f in lumen_facts}
        assert "Energy savings" in fact_names
        assert "Up to 60% in laboratory tests" in fact_names["Energy savings"]
        assert "Product warranty" in fact_names
        assert "3 years" in fact_names["Product warranty"]
    finally:
        db.close()
