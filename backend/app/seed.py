"""Synthetic Demo Data Seeder for BrandProof.
Organization: Lumen (CodeNexus India 2026 Hackathon Demo)
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.models.knowledge import ApprovedFact, Guideline
from app.models.enums import UserRole, FactStatus, GuidelineStatus

DEMO_USERS = [
    {
        "email": "admin@lumen.demo",
        "password": "LumenAdmin2026!",
        "full_name": "Lumen Admin",
        "role": UserRole.ADMIN,
    },
    {
        "email": "creator@lumen.demo",
        "password": "LumenCreator2026!",
        "full_name": "Lumen Creator",
        "role": UserRole.CREATOR,
    },
    {
        "email": "reviewer@lumen.demo",
        "password": "LumenReviewer2026!",
        "full_name": "Lumen Reviewer",
        "role": UserRole.REVIEWER,
    },
]

DEMO_FACTS = [
    {
        "fact_name": "Energy savings",
        "approved_value": "Up to 60% in laboratory tests",
        "numeric_value": 60.0,
        "numeric_operator": "<=",
        "unit": "%",
        "description": "Maximum energy efficiency reduction demonstrated under certified test parameters.",
        "category": "performance",
        "source": "Lumen Lab Test Report 2025-Q3",
        "scope": "laboratory tests",
        "required_qualifiers": ["in laboratory tests"],
        "version": 1,
        "status": FactStatus.APPROVED,
    },
    {
        "fact_name": "Product warranty",
        "approved_value": "3 years",
        "numeric_value": 3.0,
        "numeric_operator": "==",
        "unit": "years",
        "description": "Manufacturer warranty coverage against hardware defects.",
        "category": "warranty",
        "source": "Lumen Standard Warranty Terms v2.1",
        "scope": "consumer hardware",
        "required_qualifiers": ["standard consumer warranty"],
        "version": 1,
        "status": FactStatus.APPROVED,
    },
]

DEMO_GUIDELINES = [
    {
        "title": "Energy Savings Accuracy",
        "description": "Mandates factual honesty and qualifier presence for all energy claims.",
        "category": "performance",
        "rule_text": "Energy savings claims must not exceed 60% and must explicitly include the qualifier 'in laboratory tests'. Never state 80% or unconditional savings.",
        "prohibited_phrases": ["80% energy savings", "80% savings", "zero power consumption", "free electricity"],
        "required_phrases": ["in laboratory tests"],
        "source": "Lumen Brand Guidelines 2026 - Section 4",
        "status": GuidelineStatus.ACTIVE,
    },
    {
        "title": "Warranty Terminology Compliance",
        "description": "Governs approved warranty phrasing and prohibits exaggerated duration claims.",
        "category": "warranty",
        "rule_text": "Product warranty is strictly 3 years. Marketing copy must never promise a lifetime warranty or indefinite replacement.",
        "prohibited_phrases": ["lifetime warranty", "guaranteed forever", "unconditional lifetime replacement"],
        "required_phrases": ["3 years", "3-year warranty"],
        "source": "Lumen Brand Guidelines 2026 - Section 7",
        "status": GuidelineStatus.ACTIVE,
    },
]


def seed_database(db: Session = None):
    close_at_end = False
    if db is None:
        db = SessionLocal()
        close_at_end = True

    try:
        print("[SEED] Starting synthetic demo data seed for organization 'Lumen'...")

        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        if not org:
            org = Organization(
                name="Lumen",
                slug="lumen"
            )
            db.add(org)
            db.flush()
            print(f"[SEED] Created organization 'Lumen' (ID: {org.id})")
        else:
            print(f"[SEED] Organization 'Lumen' already exists (ID: {org.id})")

        # 2. Users and Memberships
        admin_user = None
        for u_data in DEMO_USERS:
            user = db.query(User).filter(User.email == u_data["email"]).first()
            if not user:
                user = User(
                    email=u_data["email"],
                    hashed_password=get_password_hash(u_data["password"]),
                    full_name=u_data["full_name"],
                    is_active=True
                )
                db.add(user)
                db.flush()
                print(f"[SEED] Created user '{u_data['email']}'")
            else:
                # Update password in case of dev reset
                user.hashed_password = get_password_hash(u_data["password"])
                db.flush()
                print(f"[SEED] User '{u_data['email']}' already exists")

            if u_data["role"] == UserRole.ADMIN:
                admin_user = user

            # Membership
            membership = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == user.id
            ).first()

            if not membership:
                membership = OrganizationMember(
                    organization_id=org.id,
                    user_id=user.id,
                    role=u_data["role"]
                )
                db.add(membership)
                db.flush()
                print(f"[SEED] Assigned role '{u_data['role'].value}' to '{u_data['email']}' in Lumen")

        # 3. Approved Facts
        for f_data in DEMO_FACTS:
            fact = db.query(ApprovedFact).filter(
                ApprovedFact.organization_id == org.id,
                ApprovedFact.fact_name == f_data["fact_name"]
            ).first()

            if not fact:
                fact = ApprovedFact(
                    organization_id=org.id,
                    fact_name=f_data["fact_name"],
                    approved_value=f_data["approved_value"],
                    numeric_value=f_data["numeric_value"],
                    numeric_operator=f_data["numeric_operator"],
                    unit=f_data["unit"],
                    description=f_data["description"],
                    category=f_data["category"],
                    source=f_data["source"],
                    scope=f_data["scope"],
                    required_qualifiers=f_data["required_qualifiers"],
                    version=f_data["version"],
                    status=f_data["status"],
                    approved_by_user_id=admin_user.id if admin_user else None
                )
                db.add(fact)
                print(f"[SEED] Seeded approved fact: '{f_data['fact_name']}' -> '{f_data['approved_value']}'")

        # 4. Guidelines
        for g_data in DEMO_GUIDELINES:
            guide = db.query(Guideline).filter(
                Guideline.organization_id == org.id,
                Guideline.title == g_data["title"]
            ).first()

            if not guide:
                guide = Guideline(
                    organization_id=org.id,
                    title=g_data["title"],
                    description=g_data["description"],
                    category=g_data["category"],
                    rule_text=g_data["rule_text"],
                    prohibited_phrases=g_data["prohibited_phrases"],
                    required_phrases=g_data["required_phrases"],
                    source=g_data["source"],
                    status=g_data["status"],
                    created_by_user_id=admin_user.id if admin_user else None,
                    approved_by_user_id=admin_user.id if admin_user else None
                )
                db.add(guide)
                print(f"[SEED] Seeded brand guideline: '{g_data['title']}'")

        db.commit()
        print("[SEED] Demo data seeding completed successfully!")

    except Exception as exc:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed demo data: {exc}")
        raise
    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    seed_database()

