"""Verification script for BrandProof database initialization.
Does NOT print database passwords or sensitive connection strings.
"""
import os
import sys
from urllib.parse import urlparse

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.knowledge import ApprovedFact, Guideline
from app.services.auth_service import AuthService
from app.schemas.auth import UserLoginRequest


def verify():
    parsed = urlparse(settings.DATABASE_URL)
    masked_netloc = f"{parsed.username or ''}:***@{parsed.hostname or 'localhost'}:{parsed.port or 5432}"
    print(f"[*] Target Database: {parsed.scheme}://{masked_netloc}{parsed.path}")

    # 1. Check connection
    try:
        with engine.connect() as conn:
            print("[+] Connection to PostgreSQL database successful.")
    except Exception as exc:
        print(f"[-] Connection failed: {exc}")
        return False

    # 2. Check Alembic version
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        config = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()

        print(f"[*] Alembic Current Revision: {current_rev}")
        print(f"[*] Alembic Expected Head:    {head_rev}")
        if current_rev == head_rev:
            print("[+] Alembic schema is up to date at head revision.")
        else:
            print(f"[-] Schema revision mismatch! Current: {current_rev}, Head: {head_rev}")
            return False
    except Exception as exc:
        print(f"[-] Failed to verify Alembic revision: {exc}")
        return False

    # 3. Check Tables
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    print(f"[*] Total Tables in public schema: {len(tables)}")
    for t in tables:
        print(f"    - {t}")

    expected_tables = {
        "alembic_version", "organizations", "users", "organization_members",
        "approved_facts", "guidelines", "submissions", "submission_revisions",
        "findings", "disputes", "review_logs", "visual_brand_configs", "visual_asset_reviews"
    }
    missing = expected_tables - set(tables)
    if missing:
        print(f"[-] Missing expected tables: {missing}")
        return False
    else:
        print("[+] All expected tables are present.")

    # 4. Check Seed Data
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        if not org:
            print("[-] Organization 'Lumen' not found!")
            return False
        print(f"[+] Found Organization: '{org.name}' (ID: {org.id}, Slug: {org.slug})")

        demo_users = [
            ("admin@lumen.demo", "LumenAdmin2026!", "admin"),
            ("creator@lumen.demo", "LumenCreator2026!", "creator"),
            ("reviewer@lumen.demo", "LumenReviewer2026!", "reviewer"),
        ]

        print("[*] Verifying Demo Users & Memberships:")
        for email, password, expected_role in demo_users:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                print(f"    [-] User {email} missing!")
                return False
            mem = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == u.id
            ).first()
            if not mem:
                print(f"    [-] Membership for {email} in Lumen missing!")
                return False
            role_val = mem.role.value if hasattr(mem.role, 'value') else str(mem.role)
            print(f"    [+] {email} -> User ID: {u.id}, Active: {u.is_active}, Role: '{role_val}'")

        fact_count = db.query(ApprovedFact).filter(ApprovedFact.organization_id == org.id).count()
        guide_count = db.query(Guideline).filter(Guideline.organization_id == org.id).count()
        print(f"[+] Approved Facts for Lumen: {fact_count}")
        print(f"[+] Brand Guidelines for Lumen: {guide_count}")

        # 5. Test Authentication
        print("[*] Testing Authentication via AuthService.login:")
        for email, password, expected_role in demo_users:
            try:
                res = AuthService.login(db, UserLoginRequest(email=email, password=password))
                role_val = res.role.value if hasattr(res.role, 'value') else str(res.role)
                print(f"    [+] {email} authenticated successfully! Role: '{role_val}', Token Type: {res.token_type}")
            except Exception as e:
                print(f"    [-] {email} authentication failed: {e}")
                return False

        print("[+] ALL CHECKS PASSED SUCCESSFULLY!")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
