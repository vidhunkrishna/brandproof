import pytest
import shutil
import subprocess
from datetime import datetime, timezone
from pydantic import ValidationError
from app.models.enums import ContentType, SubmissionStatus, FindingVerdict, ReviewLane
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionRevisionCreateRequest,
    FindingResponse,
    SubmissionRevisionResponse,
    SubmissionResponse,
    ReviewResultResponse,
)
from app.core.text_utils import (
    codepoint_to_utf16_offset,
    utf16_to_codepoint_offset,
    match_to_utf16_offsets,
    extract_utf16_substring,
)
from app.core.database import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.submission import Submission, SubmissionRevision, Finding


# --- SCHEMA VALIDATION TESTS ---

def test_submission_create_request_valid():
    """Verify that a valid submission request parses correctly."""
    req = SubmissionCreateRequest(
        title="EcoSmart Launch Copy",
        content_type=ContentType.WEBSITE_COPY,
        content_text="Our smart bulbs deliver up to 60% energy savings in laboratory tests."
    )
    assert req.title == "EcoSmart Launch Copy"
    assert req.content_type == ContentType.WEBSITE_COPY
    assert req.content_text.startswith("Our smart bulbs")


def test_submission_create_request_whitespace_rejection():
    """Verify that empty or whitespace-only title/content is rejected."""
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(
            title="   ",
            content_type=ContentType.EMAIL,
            content_text="Valid text here."
        )

    with pytest.raises(ValidationError):
        SubmissionCreateRequest(
            title="Valid Title",
            content_type=ContentType.EMAIL,
            content_text="   \n\t  "
        )


def test_submission_create_request_invalid_content_type():
    """Verify that an unsupported content type is rejected."""
    with pytest.raises(ValidationError):
        SubmissionCreateRequest(
            title="Title",
            content_type="billboard_3d",  # Invalid enum value
            content_text="Valid text."
        )


def test_finding_response_valid_offsets():
    """Verify that valid UTF-16 character offsets serialize properly."""
    f = FindingResponse(
        id="find-123",
        submission_revision_id="rev-456",
        claim_text="up to 60%",
        verdict=FindingVerdict.CORRECT,
        lane=ReviewLane.LANE_2_GROUNDED_FACT,
        explanation="Matches approved fact bounds.",
        start_offset=10,
        end_offset=19,
        created_at=datetime.now(timezone.utc)
    )
    assert f.start_offset == 10
    assert f.end_offset == 19
    assert f.verdict == FindingVerdict.CORRECT


def test_finding_response_invalid_offsets():
    """Verify that start_offset > end_offset or negative offsets trigger validation errors."""
    # 1. start_offset > end_offset
    with pytest.raises(ValidationError, match="strictly less than end_offset"):
        FindingResponse(
            id="f-1",
            submission_revision_id="r-1",
            claim_text="claim",
            verdict=FindingVerdict.CORRECT,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="explanation",
            start_offset=50,
            end_offset=20,  # Invalid: end < start
            created_at=datetime.now(timezone.utc)
        )

    # 2. Negative start_offset
    with pytest.raises(ValidationError, match="start_offset must be non-negative"):
        FindingResponse(
            id="f-2",
            submission_revision_id="r-1",
            claim_text="claim",
            verdict=FindingVerdict.CORRECT,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="explanation",
            start_offset=-5,
            end_offset=20,
            created_at=datetime.now(timezone.utc)
        )


def test_finding_response_empty_interval_rejection():
    """Verify that empty offset intervals (start_offset == end_offset) are rejected."""
    with pytest.raises(ValidationError, match="strictly less than end_offset"):
        FindingResponse(
            id="f-empty",
            submission_revision_id="r-empty",
            claim_text="empty interval claim",
            verdict=FindingVerdict.CONTRADICTED,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="Empty intervals are invalid for findings.",
            start_offset=15,
            end_offset=15,  # start_offset == end_offset is rejected
            created_at=datetime.now(timezone.utc)
        )


def test_finding_response_partial_offsets_rejection():
    """Verify that providing only start_offset or only end_offset is rejected."""
    with pytest.raises(ValidationError, match="Both start_offset and end_offset must be provided together"):
        FindingResponse(
            id="f-partial-1",
            submission_revision_id="r-1",
            claim_text="claim",
            verdict=FindingVerdict.CORRECT,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="explanation",
            start_offset=10,
            end_offset=None,
            created_at=datetime.now(timezone.utc)
        )

    with pytest.raises(ValidationError, match="Both start_offset and end_offset must be provided together"):
        FindingResponse(
            id="f-partial-2",
            submission_revision_id="r-1",
            claim_text="claim",
            verdict=FindingVerdict.CORRECT,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="explanation",
            start_offset=None,
            end_offset=25,
            created_at=datetime.now(timezone.utc)
        )


def test_finding_response_none_offsets_allowed():
    """Verify that leaving both offsets as None is allowed (e.g., document-wide finding)."""
    f = FindingResponse(
        id="f-none",
        submission_revision_id="r-none",
        claim_text="global finding",
        verdict=FindingVerdict.UNVERIFIABLE,
        lane=ReviewLane.LANE_3_ADVISORY_AI,
        explanation="No specific text span",
        start_offset=None,
        end_offset=None,
        created_at=datetime.now(timezone.utc)
    )
    assert f.start_offset is None
    assert f.end_offset is None


def test_finding_response_invalid_verdict_rejection():
    """Verify that an arbitrary or unapproved verdict string fails validation."""
    with pytest.raises(ValidationError):
        FindingResponse(
            id="f-3",
            submission_revision_id="r-1",
            claim_text="claim",
            verdict="PLAUSIBLE",  # Not in the 5 approved verdicts
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="explanation",
            created_at=datetime.now(timezone.utc)
        )


# --- UTF-16 CODE-UNIT OFFSET CONVENTION & UTILITY TESTS ---

def test_single_supplementary_emoji_before_finding():
    """Verify offset calculation with a supplementary emoji (U+1F680 > U+FFFF) before the finding."""
    text = "🚀 Our smart bulbs save up to 60% energy."
    target_claim = "up to 60% energy"
    py_start = text.index(target_claim)
    py_end = py_start + len(target_claim)

    # In Python codepoints: '🚀' is index 0 (1 codepoint). py_start is 23.
    assert py_start == 23
    # In UTF-16 code units: '🚀' takes 2 code units (surrogate pair). start_utf16 must be 24 (py_start + 1).
    start_utf16, end_utf16 = match_to_utf16_offsets(text, py_start, py_end)
    assert start_utf16 == 24
    assert end_utf16 == 24 + len(target_claim)

    extracted = extract_utf16_substring(text, start_utf16, end_utf16)
    assert extracted == target_claim


def test_multiple_supplementary_emojis_before_finding():
    """Verify offset calculation with multiple supplementary emojis before the finding."""
    # 🚀 (U+1F680), 🔥 (U+1F525), 🎉 (U+1F389) — all > 0xFFFF (2 UTF-16 code units each)
    text = "🚀🔥🎉 Lumen delivers 99.9% uptime guaranteed."
    target_claim = "99.9% uptime"
    py_start = text.index(target_claim)
    py_end = py_start + len(target_claim)

    # 3 emojis = 3 Python codepoints, but 6 UTF-16 code units (difference of +3)
    start_utf16, end_utf16 = match_to_utf16_offsets(text, py_start, py_end)
    assert start_utf16 == py_start + 3
    assert end_utf16 == py_end + 3

    extracted = extract_utf16_substring(text, start_utf16, end_utf16)
    assert extracted == target_claim


def test_supplementary_emoji_within_finding():
    """Verify offset calculation when a supplementary emoji is inside the finding itself."""
    text = "Certified by Lumen 🔬 Laboratory for extreme accuracy."
    target_claim = "Lumen 🔬 Laboratory"
    py_start = text.index(target_claim)
    py_end = py_start + len(target_claim)

    start_utf16, end_utf16 = match_to_utf16_offsets(text, py_start, py_end)
    # Target claim has 1 supplementary emoji inside, so its UTF-16 length is py length + 1
    assert end_utf16 - start_utf16 == len(target_claim) + 1

    extracted = extract_utf16_substring(text, start_utf16, end_utf16)
    assert extracted == target_claim


def test_tamil_and_indic_characters():
    """Verify offset handling for Tamil and Devanagari (BMP scripts: 1 codepoint == 1 code unit)."""
    # Tamil
    text_tamil = "Lumen தயாரிப்புகள் 60% ஆற்றல் சேமிப்பை வழங்குகின்றன."
    target_tamil = "60% ஆற்றல் சேமிப்பை"
    py_start = text_tamil.index(target_tamil)
    py_end = py_start + len(target_tamil)

    start_utf16, end_utf16 = match_to_utf16_offsets(text_tamil, py_start, py_end)
    assert start_utf16 == py_start  # In BMP, codepoints == UTF-16 code units
    assert end_utf16 == py_end
    assert extract_utf16_substring(text_tamil, start_utf16, end_utf16) == target_tamil

    # Hindi / Devanagari
    text_hindi = "Lumen ऊर्जा बचत: 60% तक की बचत प्रयोगशाला में प्रमाणित।"
    target_hindi = "60% तक की बचत"
    py_start_h = text_hindi.index(target_hindi)
    py_end_h = py_start_h + len(target_hindi)

    start_utf16_h, end_utf16_h = match_to_utf16_offsets(text_hindi, py_start_h, py_end_h)
    assert start_utf16_h == py_start_h
    assert end_utf16_h == py_end_h
    assert extract_utf16_substring(text_hindi, start_utf16_h, end_utf16_h) == target_hindi


def test_accented_characters():
    """Verify offset handling for accented European languages (French, Spanish)."""
    text_french = "Économisez jusqu'à 60% d'énergie avec notre technologie brevetée."
    target_claim = "60% d'énergie"
    py_start = text_french.index(target_claim)
    py_end = py_start + len(target_claim)

    start_utf16, end_utf16 = match_to_utf16_offsets(text_french, py_start, py_end)
    assert start_utf16 == py_start
    assert end_utf16 == py_end
    assert extract_utf16_substring(text_french, start_utf16, end_utf16) == target_claim


def test_complex_multilingual_emoji_combination_against_javascript():
    """Verify mixed supplementary emojis, Indic text, and accented text against actual JavaScript semantics."""
    text = "🚀🔥 தமிழ் 🔬 Économisez jusqu'à 60% d'énergie en laboratoire! 🎉"
    target_claim = "60% d'énergie"
    py_start = text.index(target_claim)
    py_end = py_start + len(target_claim)

    start_utf16, end_utf16 = match_to_utf16_offsets(text, py_start, py_end)
    extracted = extract_utf16_substring(text, start_utf16, end_utf16)
    assert extracted == target_claim

    # If Node.js is installed on the host, verify direct JavaScript String.prototype.substring evaluation
    node_path = shutil.which("node")
    if node_path:
        js_code = (
            f"const text = {repr(text)};"
            f"const sub = text.substring({start_utf16}, {end_utf16});"
            f"if (sub !== {repr(target_claim)}) {{"
            f"  console.error('Mismatch: ' + JSON.stringify(sub) + ' !== ' + JSON.stringify({repr(target_claim)}));"
            f"  process.exit(1);"
            f"}}"
        )
        res = subprocess.run([node_path, "-e", js_code], capture_output=True, text=True)
        assert res.returncode == 0, f"Node.js extraction failed: {res.stderr}"


def test_codepoint_to_utf16_offset_edge_cases():
    """Verify boundary conditions for offset converters."""
    text = "🚀 hello"
    # Negative index clamps to 0
    assert codepoint_to_utf16_offset(text, -1) == 0
    assert codepoint_to_utf16_offset(text, 0) == 0
    # Past length clamps to total UTF-16 code units
    assert codepoint_to_utf16_offset(text, 100) == 8
    # Round-trip conversions
    for idx in range(len(text) + 1):
        u16 = codepoint_to_utf16_offset(text, idx)
        cp = utf16_to_codepoint_offset(text, u16)
        assert cp == idx


# --- DATABASE PERSISTENCE TESTS ---

def test_db_persistence_with_finding_offsets():
    """Verify that start_offset and end_offset columns persist and retrieve accurately in PostgreSQL."""
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "lumen").first()
        user = db.query(User).filter(User.email == "creator@lumen.demo").first()
        assert org is not None and user is not None

        # Content text with an emoji before the target claim
        content = "⚡ Special offer: Check out our guaranteed lifetime warranty on all devices."
        match_phrase = "lifetime warranty"
        py_start = content.index(match_phrase)
        py_end = py_start + len(match_phrase)

        # Convert to standardized UTF-16 code-unit offsets
        start_u16, end_u16 = match_to_utf16_offsets(content, py_start, py_end)

        # Create submission
        sub = Submission(
            organization_id=org.id,
            creator_user_id=user.id,
            title="Offset Verification Submission",
            content_type=ContentType.GENERAL,
            current_status=SubmissionStatus.DRAFT
        )
        db.add(sub)
        db.flush()

        # Create revision
        rev = SubmissionRevision(
            submission_id=sub.id,
            revision_number=1,
            content_text=content,
            overall_verdict="CONTRADICTED"
        )
        db.add(rev)
        db.flush()

        # Create finding with UTF-16 offsets
        finding = Finding(
            submission_revision_id=rev.id,
            claim_text=match_phrase,
            verdict=FindingVerdict.CONTRADICTED,
            lane=ReviewLane.LANE_1_DETERMINISTIC,
            explanation="Lifetime warranty is forbidden. Approved term is 3 years.",
            start_offset=start_u16,
            end_offset=end_u16
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)

        # Assert offsets are accurately stored and extract_utf16_substring reproduces exact claim
        assert finding.start_offset == start_u16
        assert finding.end_offset == end_u16
        assert extract_utf16_substring(rev.content_text, finding.start_offset, finding.end_offset) == match_phrase
    finally:
        db.close()
