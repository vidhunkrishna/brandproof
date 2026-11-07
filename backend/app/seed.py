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
from app.models.submission import Submission, SubmissionRevision, Finding, Dispute, ReviewLog
from app.models.visual import VisualBrandConfig, VisualAssetReview
from app.models.enums import (
    UserRole,
    FactStatus,
    GuidelineStatus,
    ContentType,
    SubmissionStatus,
    FindingVerdict,
    RevisionVerdict,
    ReviewLane,
    DisputeStatus,
)

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
    {
        "fact_name": "Bulb lifespan",
        "approved_value": "25,000 hours under standard residential usage",
        "numeric_value": 25000.0,
        "numeric_operator": ">=",
        "unit": "hours",
        "description": "Rated LED diode operating lifespan calculated under standard duty cycles.",
        "category": "durability",
        "source": "Lumen Accelerated Life Testing Report v1.4",
        "scope": "residential usage",
        "required_qualifiers": ["standard residential usage"],
        "version": 1,
        "status": FactStatus.APPROVED,
    },
    {
        "fact_name": "Standby power consumption",
        "approved_value": "0.5 W maximum in idle wireless mode",
        "numeric_value": 0.5,
        "numeric_operator": "<=",
        "unit": "W",
        "description": "Parasitic standby energy draw while connected to mesh network.",
        "category": "electrical",
        "source": "Lumen Low-Power Hardware Spec 2025",
        "scope": "idle wireless mode",
        "required_qualifiers": ["in idle wireless mode"],
        "version": 1,
        "status": FactStatus.APPROVED,
    },
    {
        "fact_name": "Color temperature range",
        "approved_value": "2200K to 6500K tunable white spectrum",
        "numeric_value": None,
        "numeric_operator": None,
        "unit": "K",
        "description": "Correlated color temperature adjustment range for tunable white series.",
        "category": "optical",
        "source": "Lumen Optical Spectrum Datasheet 2025-RevB",
        "scope": "tunable white series",
        "required_qualifiers": ["tunable white"],
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
    {
        "title": "Lifespan Claims Policy",
        "description": "Ensures operating lifespan claims reflect verified testing limits.",
        "category": "durability",
        "rule_text": "Lifespan claims must never promise infinite duration or bulbs that never burn out.",
        "prohibited_phrases": ["never burn out", "infinite lifespan", "lasts forever"],
        "required_phrases": [],
        "source": "Lumen Brand Guidelines 2026 - Section 5",
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
        users_by_role = {}
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
                user.hashed_password = get_password_hash(u_data["password"])
                db.flush()
                print(f"[SEED] User '{u_data['email']}' already exists")

            users_by_role[u_data["role"]] = user

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

        admin_user = users_by_role.get(UserRole.ADMIN)
        creator_user = users_by_role.get(UserRole.CREATOR)
        reviewer_user = users_by_role.get(UserRole.REVIEWER)

        # 3. Approved Facts
        facts_by_name = {}
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
                    approved_by_user_id=admin_user.id if admin_user else None,
                    approved_at=datetime.now(timezone.utc)
                )
                db.add(fact)
                db.flush()
                print(f"[SEED] Seeded approved fact: '{f_data['fact_name']}' -> '{f_data['approved_value']}'")
            else:
                if not fact.approved_at:
                    fact.approved_at = datetime.now(timezone.utc)
                    fact.approved_by_user_id = admin_user.id if admin_user else None
                    db.flush()

            facts_by_name[f_data["fact_name"]] = fact

        # 4. Guidelines
        guidelines_by_title = {}
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
                    approved_by_user_id=admin_user.id if admin_user else None,
                    approved_at=datetime.now(timezone.utc)
                )
                db.add(guide)
                db.flush()
                print(f"[SEED] Seeded brand guideline: '{g_data['title']}'")
            else:
                guide.prohibited_phrases = g_data["prohibited_phrases"]
                guide.required_phrases = g_data["required_phrases"]
                guide.rule_text = g_data["rule_text"]
                if not guide.approved_at:
                    guide.approved_at = datetime.now(timezone.utc)
                    guide.approved_by_user_id = admin_user.id if admin_user else None
                db.flush()

            guidelines_by_title[g_data["title"]] = guide

        # Clean up any stale/conflicting guidelines
        for stale_title in ["Smart Home Compatibility Statements", "Lifespan and Durability Claims"]:
            stale_g = db.query(Guideline).filter(Guideline.organization_id == org.id, Guideline.title == stale_title).first()
            if stale_g:
                db.delete(stale_g)
                db.flush()

        # 5. Visual Brand Config
        visual_cfg = db.query(VisualBrandConfig).filter(
            VisualBrandConfig.organization_id == org.id
        ).first()

        if not visual_cfg:
            visual_cfg = VisualBrandConfig(
                organization_id=org.id,
                approved_colors=["#4F46E5", "#6366F1", "#1E1B4B", "#F8FAFC", "#FFFFFF"],
                approved_fonts=["Inter", "system-ui", "sans-serif"],
                primary_logo_aspect_ratio=3.0,
                secondary_logo_aspect_ratio=1.0,
                minimum_contrast_ratio=4.5,
            )
            db.add(visual_cfg)
            db.flush()
            print("[SEED] Seeded Lumen visual brand configuration.")

        # Sample Visual Asset Review
        sample_review = db.query(VisualAssetReview).filter(
            VisualAssetReview.organization_id == org.id,
            VisualAssetReview.filename == "lumen_spring_hero_banner.png"
        ).first()

        if not sample_review:
            sample_review = VisualAssetReview(
                organization_id=org.id,
                created_by_user_id=admin_user.id if admin_user else None,
                filename="lumen_spring_hero_banner.png",
                content_type="image/png",
                byte_size=148200,
                width=1200,
                height=630,
                detected_format="PNG",
                findings_json=[
                    {
                        "type": "contrast",
                        "status": "pass",
                        "ratio": 7.2,
                        "issue": "Text contrast ratio 7.2:1 exceeds WCAG AA requirement (4.5:1)."
                    },
                    {
                        "type": "palette",
                        "status": "pass",
                        "issue": "Detected dominant brand colors #4F46E5 and #1E1B4B match Lumen color token system."
                    }
                ]
            )
            db.add(sample_review)
            db.flush()
            print("[SEED] Seeded sample visual asset review.")

        # 6. Demo Submissions, Revisions, Findings, and Disputes
        energy_fact = facts_by_name.get("Energy savings")
        warranty_guide = guidelines_by_title.get("Warranty Terminology Compliance")
        lifespan_guide = guidelines_by_title.get("Lifespan Claims Policy")

        # Submission 1: Launch Announcement (Disputed Claim on Quantum Mesh)
        sub1 = db.query(Submission).filter(
            Submission.organization_id == org.id,
            Submission.title == "Lumen Smart Bulb Launch Announcement"
        ).first()

        if not sub1 and creator_user:
            sub1 = Submission(
                organization_id=org.id,
                creator_user_id=creator_user.id,
                title="Lumen Smart Bulb Launch Announcement",
                content_type=ContentType.WEBSITE_COPY,
                current_status=SubmissionStatus.DISPUTED,
            )
            db.add(sub1)
            db.flush()

            c1_text = (
                "Upgrade to Lumen Smart Bulb today! Experience up to 60% energy savings in laboratory tests "
                "and enjoy our unconditional lifetime warranty. Plus, our lights sync with quantum mesh networks seamlessly."
            )
            rev1 = SubmissionRevision(
                submission_id=sub1.id,
                revision_number=1,
                content_text=c1_text,
                change_summary="Initial website marketing draft submission.",
                overall_verdict=RevisionVerdict.NEEDS_REVIEW,
                review_used_fallback=False,
            )
            db.add(rev1)
            db.flush()

            # Finding 1: Correct energy savings
            f1 = Finding(
                submission_revision_id=rev1.id,
                claim_text="up to 60% energy savings in laboratory tests",
                verdict=FindingVerdict.CORRECT,
                lane=ReviewLane.LANE_2_GROUNDED_FACT,
                explanation="Matches approved fact 'Energy savings' (Up to 60% in laboratory tests) with all required qualifiers present.",
                suggested_correction=None,
                fact_id=energy_fact.id if energy_fact else None,
                confidence_score=0.98,
                start_offset=46,
                end_offset=90,
            )
            db.add(f1)

            # Finding 2: Contradicted lifetime warranty
            f2 = Finding(
                submission_revision_id=rev1.id,
                claim_text="unconditional lifetime warranty",
                verdict=FindingVerdict.CONTRADICTED,
                lane=ReviewLane.LANE_1_DETERMINISTIC,
                explanation="Violates guideline 'Warranty Terminology Compliance'. Product warranty is strictly 3 years. Marketing copy must never promise a lifetime warranty.",
                suggested_correction="3-year standard limited warranty",
                guideline_id=warranty_guide.id if warranty_guide else None,
                confidence_score=1.0,
                start_offset=105,
                end_offset=136,
            )
            db.add(f2)

            # Finding 3: Unsupported quantum mesh -> DISPUTE RAISED
            f3 = Finding(
                submission_revision_id=rev1.id,
                claim_text="sync with quantum mesh networks seamlessly",
                verdict=FindingVerdict.UNSUPPORTED,
                lane=ReviewLane.LANE_3_ADVISORY_AI,
                explanation="Quantum mesh synchronization is not substantiated by any registered product specification or lab report in the approved facts registry.",
                suggested_correction="sync with certified Matter and Thread wireless standards",
                confidence_score=0.88,
                start_offset=155,
                end_offset=197,
            )
            db.add(f3)
            db.flush()

            # Create an open Dispute on Finding 3 so the Reviewer role has a live dispute to inspect and resolve
            disp = Dispute(
                organization_id=org.id,
                finding_id=f3.id,
                raised_by_user_id=creator_user.id,
                reason="Our next-generation Thread radio architecture utilizes quantum-resistant key exchange mesh protocols certified under IEEE 802.15.4 Annex G. Requesting reviewer exception or fact registry update.",
                status=DisputeStatus.OPEN,
            )
            db.add(disp)
            db.flush()

            db.add(ReviewLog(
                organization_id=org.id,
                submission_id=sub1.id,
                user_id=creator_user.id,
                action="dispute_created",
                comment=disp.reason,
                metadata_json={"dispute_id": disp.id, "finding_id": f3.id, "original_verdict": f3.verdict.value}
            ))

            print("[SEED] Seeded Submission 1 ('Lumen Smart Bulb Launch Announcement') with live open Dispute.")

        # Submission 2: Approved Package (100% Correct Claims)
        sub2 = db.query(Submission).filter(
            Submission.organization_id == org.id,
            Submission.title == "Lumen Residential Living Room Package"
        ).first()

        if not sub2 and creator_user:
            sub2 = Submission(
                organization_id=org.id,
                creator_user_id=creator_user.id,
                title="Lumen Residential Living Room Package",
                content_type=ContentType.SOCIAL_MEDIA,
                current_status=SubmissionStatus.APPROVED,
            )
            db.add(sub2)
            db.flush()

            c2_text = (
                "Transform your home with Lumen Smart Lighting. Cut electricity by up to 60% in laboratory tests "
                "and count on our 3-year warranty for peace of mind."
            )
            rev2 = SubmissionRevision(
                submission_id=sub2.id,
                revision_number=1,
                content_text=c2_text,
                change_summary="Approved social campaign draft.",
                overall_verdict=RevisionVerdict.CORRECT,
                review_used_fallback=False,
            )
            db.add(rev2)
            db.flush()

            db.add(Finding(
                submission_revision_id=rev2.id,
                claim_text="up to 60% in laboratory tests",
                verdict=FindingVerdict.CORRECT,
                lane=ReviewLane.LANE_2_GROUNDED_FACT,
                explanation="Fully grounded in approved fact 'Energy savings'. Laboratory qualifier correctly cited.",
                fact_id=energy_fact.id if energy_fact else None,
                confidence_score=0.99,
                start_offset=66,
                end_offset=95,
            ))

            db.add(Finding(
                submission_revision_id=rev2.id,
                claim_text="3-year warranty",
                verdict=FindingVerdict.CORRECT,
                lane=ReviewLane.LANE_1_DETERMINISTIC,
                explanation="Complies with brand warranty policy and matches registered 3-year standard coverage.",
                guideline_id=warranty_guide.id if warranty_guide else None,
                confidence_score=1.0,
                start_offset=113,
                end_offset=128,
            ))

            db.add(ReviewLog(
                organization_id=org.id,
                submission_id=sub2.id,
                user_id=admin_user.id if admin_user else creator_user.id,
                action="approve",
                comment="All claims verified and grounded against approved knowledge base.",
            ))

            print("[SEED] Seeded Submission 2 ('Lumen Residential Living Room Package') with APPROVED status.")

        # Submission 3: Changes Requested (Contradicted Claims)
        sub3 = db.query(Submission).filter(
            Submission.organization_id == org.id,
            Submission.title == "Lumen Ultra Eco Campaign Email"
        ).first()

        if not sub3 and creator_user:
            sub3 = Submission(
                organization_id=org.id,
                creator_user_id=creator_user.id,
                title="Lumen Ultra Eco Campaign Email",
                content_type=ContentType.EMAIL,
                current_status=SubmissionStatus.CHANGES_REQUESTED,
            )
            db.add(sub3)
            db.flush()

            c3_text = "Get our new bulbs that never burn out and save 80% on your lighting power bills without compromise!"
            rev3 = SubmissionRevision(
                submission_id=sub3.id,
                revision_number=1,
                content_text=c3_text,
                change_summary="Initial promotional newsletter draft.",
                overall_verdict=RevisionVerdict.CONTRADICTED,
                review_used_fallback=False,
            )
            db.add(rev3)
            db.flush()

            db.add(Finding(
                submission_revision_id=rev3.id,
                claim_text="never burn out",
                verdict=FindingVerdict.CONTRADICTED,
                lane=ReviewLane.LANE_1_DETERMINISTIC,
                explanation="Violates guideline 'Lifespan Claims Policy'. Lumen bulbs are rated for 25,000 hours under standard residential usage.",
                suggested_correction="rated for 25,000 hours of reliable lighting",
                guideline_id=lifespan_guide.id if lifespan_guide else None,
                confidence_score=1.0,
                start_offset=23,
                end_offset=37,
            ))

            db.add(Finding(
                submission_revision_id=rev3.id,
                claim_text="save 80% on your lighting power bills",
                verdict=FindingVerdict.CONTRADICTED,
                lane=ReviewLane.LANE_2_GROUNDED_FACT,
                explanation="Exceeds maximum approved energy savings fact (60%) and omits the mandatory 'in laboratory tests' qualifier.",
                suggested_correction="save up to 60% in laboratory tests",
                fact_id=energy_fact.id if energy_fact else None,
                confidence_score=0.96,
                start_offset=42,
                end_offset=79,
            ))

            db.add(ReviewLog(
                organization_id=org.id,
                submission_id=sub3.id,
                user_id=reviewer_user.id if reviewer_user else creator_user.id,
                action="request_changes",
                comment="Claims contradict active guidelines and approved facts. Please correct before resubmitting.",
            ))

            print("[SEED] Seeded Submission 3 ('Lumen Ultra Eco Campaign Email') with CHANGES_REQUESTED status.")

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
