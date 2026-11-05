import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.organization import Organization
from app.models.knowledge import Guideline, ApprovedFact
from app.models.enums import GuidelineStatus, FactStatus, FindingVerdict, ReviewLane
from app.review_engine.deterministic import DeterministicReviewEngine
from app.review_engine.fact_checker import GroundedFactChecker
from app.core.text_utils import extract_utf16_substring


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def lumen_org(db):
    org = db.query(Organization).filter(Organization.slug == "lumen").first()
    assert org is not None, "Synthetic demo organization 'Lumen' must exist (run seed if missing)"
    return org


# ==============================================================================
# LANE 1: DETERMINISTIC GUIDELINE ENGINE TESTS
# ==============================================================================

def test_lane1_prohibited_phrase_detection(db, lumen_org):
    """Verify that a prohibited phrase is detected with exact guideline grounding and offsets."""
    text = "Our home automation devices come with a lifetime warranty on all components."
    findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text)

    assert len(findings) >= 1
    f = next((item for item in findings if item.claim_text.lower() == "lifetime warranty"), None)
    assert f is not None
    assert f.verdict == FindingVerdict.CONTRADICTED
    assert f.lane == ReviewLane.LANE_1_DETERMINISTIC
    assert f.guideline_title == "Warranty Terminology Compliance"
    assert f.guideline_id is not None
    assert f.guideline_version == 1
    assert "lifetime warranty" in f.explanation.lower()
    assert f.suggested_correction is not None
    assert "3 years" in f.suggested_correction

    # Verify exact JavaScript substring extraction
    extracted = extract_utf16_substring(text, f.start_offset, f.end_offset)
    assert extracted == "lifetime warranty"


def test_lane1_case_insensitive_matching(db, lumen_org):
    """Verify that prohibited phrase detection is case-insensitive."""
    text = "Enjoy ZERO POWER CONSUMPTION with our revolutionary smart sensor technology."
    findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text)

    f = next((item for item in findings if "zero power consumption" in item.claim_text.lower()), None)
    assert f is not None
    assert f.verdict == FindingVerdict.CONTRADICTED
    assert f.claim_text == "ZERO POWER CONSUMPTION"

    extracted = extract_utf16_substring(text, f.start_offset, f.end_offset)
    assert extracted == "ZERO POWER CONSUMPTION"


def test_lane1_word_boundary_behavior(db, lumen_org):
    """Verify that partial words do not trigger false positive violations."""
    # Create a temporary guideline with prohibited phrase 'eco'
    temp_g = Guideline(
        organization_id=lumen_org.id,
        title="Eco Naming Policy",
        rule_text="Do not use standalone term 'eco'.",
        category="branding",
        prohibited_phrases=["eco"],
        status=GuidelineStatus.ACTIVE,
        version=1,
    )
    db.add(temp_g)
    db.commit()

    try:
        # 'economy' contains 'eco' as a prefix, but must NOT match due to word boundaries
        text_safe = "Our economy bulbs reduce electricity bills significantly."
        safe_findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text_safe)
        eco_findings_safe = [f for f in safe_findings if f.guideline_id == temp_g.id]
        assert len(eco_findings_safe) == 0

        # Standalone 'eco' must match
        text_violating = "Try our new eco bulbs today."
        violating_findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text_violating)
        eco_findings_viol = [f for f in violating_findings if f.guideline_id == temp_g.id]
        assert len(eco_findings_viol) == 1
        assert eco_findings_viol[0].claim_text == "eco"
        assert extract_utf16_substring(text_violating, eco_findings_viol[0].start_offset, eco_findings_viol[0].end_offset) == "eco"
    finally:
        db.delete(temp_g)
        db.commit()
def test_lane1_required_phrase_detection(db, lumen_org):
    """Verify that required phrases are enforced when relevant topic is discussed, and ignored when irrelevant."""
    # 1. Relevant text discussing energy savings but missing 'in laboratory tests'
    text_missing = "Our smart bulbs deliver up to 50% energy savings across households."
    findings_missing = DeterministicReviewEngine.evaluate(db, lumen_org.id, text_missing)
    f_missing = next((f for f in findings_missing if "in laboratory tests" in f.explanation.lower()), None)
    assert f_missing is not None
    assert f_missing.verdict == FindingVerdict.CONTRADICTED
    assert f_missing.guideline_title == "Energy Savings Accuracy"
    assert "in laboratory tests" in f_missing.suggested_correction

    # 2. Text containing the required qualifier -> No required phrase violation
    text_compliant = "Our smart bulbs deliver up to 50% energy savings in laboratory tests."
    findings_compliant = DeterministicReviewEngine.evaluate(db, lumen_org.id, text_compliant)
    f_compliant_req = [f for f in findings_compliant if f.guideline_title == "Energy Savings Accuracy" and "in laboratory tests" in f.explanation]
    assert len(f_compliant_req) == 0

    # 3. Completely unrelated text -> Must NOT trigger required phrase violation
    text_unrelated = "Our mobile app received a major design update with dark mode support."
    findings_unrelated = DeterministicReviewEngine.evaluate(db, lumen_org.id, text_unrelated)
    assert len(findings_unrelated) == 0


def test_lane1_utf16_offsets_with_emojis_before_finding(db, lumen_org):
    """Verify that finding offsets are exact UTF-16 code units even with supplementary emojis preceding."""
    # 🚀 and 🔥 are supplementary characters (> U+FFFF), each taking 2 UTF-16 code units
    text = "🚀🔥 Check out our guaranteed lifetime warranty on all devices!"
    findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text)

    f = next((item for item in findings if item.claim_text.lower() == "lifetime warranty"), None)
    assert f is not None
    extracted = extract_utf16_substring(text, f.start_offset, f.end_offset)
    assert extracted == "lifetime warranty"


def test_lane1_multiple_findings_in_one_submission(db, lumen_org):
    """Verify that multiple prohibited phrases in one document generate multiple orderly findings."""
    text = "We promise free electricity for homes and guaranteed forever coverage on parts."
    findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text)

    claims = [f.claim_text.lower() for f in findings]
    assert "free electricity" in claims
    assert "guaranteed forever" in claims
    # Verify sorted in order of offsets
    assert findings[0].start_offset < findings[1].start_offset


def test_lane1_cross_org_guideline_isolation(db, lumen_org):
    """Verify that guidelines from one organization never leak to another."""
    # Create another organization
    other_org = db.query(Organization).filter(Organization.slug == "competitor-lane1").first()
    if not other_org:
        other_org = Organization(name="Competitor Lane 1", slug="competitor-lane1")
        db.add(other_org)
        db.flush()

    competitor_guideline = Guideline(
        organization_id=other_org.id,
        title="Competitor Strict Prohibition",
        rule_text="Never mention competitors.",
        category="general",
        prohibited_phrases=["secret competitor phrase"],
        status=GuidelineStatus.ACTIVE,
        version=1,
    )
    db.add(competitor_guideline)
    db.commit()

    try:
        text = "This copy contains secret competitor phrase for review."
        # Lumen evaluation must NOT detect competitor's guideline
        lumen_findings = DeterministicReviewEngine.evaluate(db, lumen_org.id, text)
        assert not any(f.claim_text == "secret competitor phrase" for f in lumen_findings)

        # Other org evaluation MUST detect it
        other_findings = DeterministicReviewEngine.evaluate(db, other_org.id, text)
        assert any(f.claim_text == "secret competitor phrase" for f in other_findings)
    finally:
        db.delete(competitor_guideline)
        db.delete(other_org)
        db.commit()
# ==============================================================================
# LANE 2: GROUNDED FACT VERIFICATION TESTS
# ==============================================================================

def test_lane2_approved_energy_claim_correct(db, lumen_org):
    """Verify that an approved energy claim matching numeric bounds and qualifier evaluates to CORRECT."""
    text = "Our smart bulbs save up to 60% in laboratory tests."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    assert len(findings) == 1
    f = findings[0]
    assert f.verdict == FindingVerdict.CORRECT
    assert f.lane == ReviewLane.LANE_2_GROUNDED_FACT
    assert f.fact_name == "Energy savings"
    assert f.fact_version == 1
    assert "verified" in f.explanation.lower()
    assert extract_utf16_substring(text, f.start_offset, f.end_offset) == text


def test_lane2_overstated_energy_claim_contradicted(db, lumen_org):
    """Verify that an overstated claim exceeding approved numeric bound evaluates to CONTRADICTED."""
    text = "Save up to 80% in laboratory tests with our latest system."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    f = next((item for item in findings if item.fact_name == "Energy savings"), None)
    assert f is not None
    assert f.verdict == FindingVerdict.CONTRADICTED
    assert f.lane == ReviewLane.LANE_2_GROUNDED_FACT
    assert "exceeds approved limit" in f.explanation
    assert f.suggested_correction is not None
    assert "60" in f.suggested_correction


def test_lane2_missing_required_qualifier_contradicted(db, lumen_org):
    """Verify that a claim clearly referring to an approved fact is CONTRADICTED if required qualifier is omitted."""
    text = "Save up to 60% on all smart bulb energy costs."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    f = next((item for item in findings if item.fact_name == "Energy savings"), None)
    assert f is not None
    assert f.verdict == FindingVerdict.CONTRADICTED
    assert "omits mandatory qualifier" in f.explanation
    assert "in laboratory tests" in f.explanation
    assert f.suggested_correction is not None
    assert "in laboratory tests" in f.suggested_correction


def test_lane2_three_year_warranty_with_lifetime_claim_unverifiable(db, lumen_org):
    """Verify that 'Lifetime warranty' is NOT converted into fake numeric years; evaluated as UNVERIFIABLE in Lane 2."""
    text = "Our lights include a lifetime warranty for all customers."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    f = next((item for item in findings if item.fact_name == "Product warranty"), None)
    assert f is not None
    assert f.verdict == FindingVerdict.UNVERIFIABLE
    assert f.lane == ReviewLane.LANE_2_GROUNDED_FACT
    assert "cannot be verified against approved numeric fact" in f.explanation


def test_lane2_draft_and_pending_facts_ignored(db, lumen_org):
    """Verify that draft or pending facts are NEVER used as approved evidence."""
    pending_fact = ApprovedFact(
        organization_id=lumen_org.id,
        fact_name="Solar conversion efficiency",
        approved_value="Up to 45%",
        numeric_value=45.0,
        numeric_operator="<=",
        unit="%",
        category="performance",
        status=FactStatus.PENDING_APPROVAL,  # Pending approval!
        version=1,
    )
    db.add(pending_fact)
    db.commit()

    try:
        text = "Our panels achieve 45% solar conversion efficiency."
        findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

        # Must NOT be marked CORRECT using the pending fact
        correct_finding = next((f for f in findings if f.verdict == FindingVerdict.CORRECT and f.fact_name == pending_fact.fact_name), None)
        assert correct_finding is None
    finally:
        db.delete(pending_fact)
        db.commit()
def test_lane2_superseded_fact_identified_as_outdated(db, lumen_org):
    """Verify that claims tied to superseded facts produce OUTDATED verdicts with update suggestions."""
    # Create Fact v1 (superseded) and Fact v2 (approved)
    v1_fact = ApprovedFact(
        organization_id=lumen_org.id,
        fact_name="Cloud response latency",
        approved_value="Under 50ms",
        numeric_value=50.0,
        numeric_operator="<=",
        unit="ms",
        category="performance",
        status=FactStatus.SUPERSEDED,
        version=1,
    )
    db.add(v1_fact)
    db.flush()

    v2_fact = ApprovedFact(
        organization_id=lumen_org.id,
        fact_name="Cloud response latency",
        approved_value="Under 20ms",
        numeric_value=20.0,
        numeric_operator="<=",
        unit="ms",
        category="performance",
        status=FactStatus.APPROVED,
        version=2,
    )
    v1_fact.superseded_by_id = v2_fact.id
    db.add(v2_fact)
    db.commit()

    try:
        # A claim referencing the superseded v1 specification
        text = "Lumen provides fast cloud response latency under 50ms."
        findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

        f_outdated = next((f for f in findings if f.fact_id == v1_fact.id or f.fact_name == "Cloud response latency"), None)
        assert f_outdated is not None
        assert f_outdated.verdict == FindingVerdict.OUTDATED
        assert "superseded" in f_outdated.explanation.lower()
        assert f_outdated.suggested_correction is not None
        assert "20ms" in f_outdated.suggested_correction
    finally:
        db.delete(v1_fact)
        db.delete(v2_fact)
        db.commit()
def test_lane2_expired_fact_produces_outdated(db, lumen_org):
    """Verify that an expired approved fact evaluates to OUTDATED."""
    past_date = datetime.now(timezone.utc) - timedelta(days=30)
    expired_fact = ApprovedFact(
        organization_id=lumen_org.id,
        fact_name="Seasonal energy discount",
        approved_value="25% discount",
        numeric_value=25.0,
        numeric_operator="<=",
        unit="%",
        category="pricing",
        status=FactStatus.APPROVED,
        valid_until=past_date,  # Expired 30 days ago
        version=1,
    )
    db.add(expired_fact)
    db.commit()

    try:
        text = "Save 25% with our seasonal energy discount."
        findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

        f_expired = next((f for f in findings if f.fact_id == expired_fact.id), None)
        assert f_expired is not None
        assert f_expired.verdict == FindingVerdict.OUTDATED
        assert "expired" in f_expired.explanation.lower()
    finally:
        db.delete(expired_fact)
        db.commit()


def test_lane2_incompatible_units_not_compared(db, lumen_org):
    """Verify that facts and claims with incompatible units (e.g. hours vs %) are never compared."""
    # Text mentions 50,000 hours of lifespan
    text = "Our bulbs run continuously for 50000 hours."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    # Must NOT compare 50000 hours against 'Energy savings' (which has unit '%')
    energy_contradiction = next((f for f in findings if f.fact_name == "Energy savings"), None)
    assert energy_contradiction is None


def test_lane2_claims_without_identifiable_fact_not_marked_correct(db, lumen_org):
    """Verify that clearly identifiable factual claims without approved registry facts are marked UNSUPPORTED, not CORRECT."""
    text = "We are the undisputed market leader with 99.8% customer satisfaction."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    assert len(findings) >= 1
    f = findings[0]
    assert f.verdict == FindingVerdict.UNSUPPORTED
    assert f.verdict != FindingVerdict.CORRECT
    assert "no corresponding approved fact" in f.explanation.lower()


def test_lane2_ambiguous_claim_evaluates_to_unverifiable(db, lumen_org):
    """Verify that ambiguous or unmatchable marketing claims evaluate to UNVERIFIABLE."""
    text = "We are the #1 smart home market leader worldwide."
    findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)

    assert len(findings) >= 1
    f = findings[0]
    assert f.verdict == FindingVerdict.UNVERIFIABLE
    assert f.verdict != FindingVerdict.CORRECT
    assert "ambiguous or unmatchable" in f.explanation.lower()


def test_lane2_cross_org_fact_isolation(db, lumen_org):
    """Verify that facts from one organization are completely isolated from another."""
    other_org = db.query(Organization).filter(Organization.slug == "competitor-lane2").first()
    if not other_org:
        other_org = Organization(name="Competitor Lane 2", slug="competitor-lane2")
        db.add(other_org)
        db.flush()

    comp_fact = ApprovedFact(
        organization_id=other_org.id,
        fact_name="Carbon footprint reduction",
        approved_value="Reduced by 75%",
        numeric_value=75.0,
        numeric_operator="<=",
        unit="%",
        category="performance",
        status=FactStatus.APPROVED,
        version=1,
    )
    db.add(comp_fact)
    db.commit()

    try:
        text = "Reduced by 75% carbon footprint reduction across production."
        # Lumen evaluation must NOT be able to verify using competitor's fact
        lumen_findings = GroundedFactChecker.evaluate(db, lumen_org.id, text)
        assert not any(f.fact_id == comp_fact.id for f in lumen_findings)

        # Other org CAN verify using its own fact
        other_findings = GroundedFactChecker.evaluate(db, other_org.id, text)
        assert any(f.fact_id == comp_fact.id and f.verdict == FindingVerdict.CORRECT for f in other_findings)
    finally:
        db.delete(comp_fact)
        db.delete(other_org)
        db.commit()
