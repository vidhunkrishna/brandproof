"""
Lane 1 — Deterministic Guideline Review Engine for BrandProof.

Evaluates marketing content strictly against active, human-approved brand guidelines:
- Matches prohibited phrases case-insensitively using zero-width boundary matching.
- Detects required phrases and mandatory qualifiers when their associated category/topic is relevant.
- Employs UTF-16 code-unit offsets [start_offset, end_offset) for exact JavaScript substring compatibility.
- Links every finding to the exact guideline ID and version.
- Operates deterministically with zero LLM dependency.
"""
import re
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from app.models.knowledge import Guideline
from app.models.enums import GuidelineStatus, FindingVerdict, ReviewLane
from app.review_engine.models import EngineFinding
from app.core.text_utils import match_to_utf16_offsets


# Generic English stopwords to exclude when extracting topic keywords from titles
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with", "by", "at",
    "to", "from", "is", "are", "be", "this", "that", "all", "our", "must", "not",
    "accuracy", "compliance", "guidelines", "guideline", "rules", "policy", "terms",
    "terminology", "usage", "standards"
}


def compile_phrase_pattern(phrase: str) -> re.Pattern:
    """
    Compile a regex pattern for phrase matching with zero-width word/whitespace boundaries.
    Prevents accidental partial-word matches (e.g. 'eco' matching 'economy', 'best' matching 'asbestos').
    Does not consume surrounding spaces, preserving exact match start/end positions.
    """
    phrase_clean = phrase.strip()
    escaped = re.escape(phrase_clean)
    prefix = r"(?<!\w)" if re.match(r"^\w", phrase_clean) else r"(?<!\S)"
    suffix = r"(?!\w)" if re.search(r"\w$", phrase_clean) else r"(?!\S)"
    return re.compile(rf"{prefix}{escaped}{suffix}", re.IGNORECASE)


def extract_relevance_keywords(guideline: Guideline) -> Set[str]:
    """
    Extract meaningful topic keywords from guideline category and title
    to determine whether content is discussing the guideline's subject matter.
    """
    keywords: Set[str] = set()

    # Category words
    if guideline.category and guideline.category.lower() not in ("general", "misc", "other"):
        for word in re.findall(r"\b\w{3,}\b", guideline.category.lower()):
            if word not in STOPWORDS:
                keywords.add(word)

    # Title words
    if guideline.title:
        for word in re.findall(r"\b\w{3,}\b", guideline.title.lower()):
            if word not in STOPWORDS:
                keywords.add(word)

    # Stemming / synonyms for common brand topics
    expanded: Set[str] = set(keywords)
    for kw in keywords:
        if kw.startswith("saving") or kw.startswith("save"):
            expanded.update(["save", "saving", "savings"])
        elif kw.startswith("warrant"):
            expanded.update(["warranty", "guarantee", "warranties"])
        elif kw.startswith("energi") or kw.startswith("energy"):
            expanded.update(["energy", "power", "electricity"])
        elif kw.startswith("perform"):
            expanded.update(["performance", "speed", "efficiency"])

    return expanded


def split_sentences_with_offsets(text: str) -> List[tuple[str, int, int]]:
    """
    Split text into sentences while tracking exact codepoint start and end positions.
    Safely preserves decimal numbers (e.g. 99.9%, $3.50) without treating internal periods as boundaries.
    """
    sentence_spans = []
    # Match sentences ending with ., !, ?, newlines, or end of text, excluding periods followed by digits
    pattern = re.compile(r"(?:[^\.!\?\n]|\.(?=\d))+(?:[.!?](?=\s|$)|[\n\r]+|$)", re.MULTILINE)
    for m in pattern.finditer(text):
        s_text = m.group()
        if not s_text.strip():
            continue
        # Trim leading/trailing whitespace for clean display while adjusting offsets
        leading_spaces = len(s_text) - len(s_text.lstrip())
        trailing_spaces = len(s_text) - len(s_text.rstrip())
        start = m.start() + leading_spaces
        end = m.end() - trailing_spaces
        if start < end:
            sentence_spans.append((text[start:end], start, end))
    return sentence_spans


class DeterministicReviewEngine:
    @staticmethod
    def get_active_guidelines(db: Session, organization_id: str) -> List[Guideline]:
        """
        Query only active guidelines belonging to the authenticated organization.
        Draft, pending, and archived guidelines are strictly excluded.
        """
        return (
            db.query(Guideline)
            .filter(
                Guideline.organization_id == organization_id,
                Guideline.status == GuidelineStatus.ACTIVE,
            )
            .all()
        )

    @classmethod
    def evaluate(
        cls,
        db: Session,
        organization_id: str,
        content_text: str,
    ) -> List[EngineFinding]:
        """
        Execute Lane 1 deterministic review against all active guidelines for the organization.
        """
        if not content_text or not content_text.strip():
            return []

        guidelines = cls.get_active_guidelines(db, organization_id)
        findings: List[EngineFinding] = []
        covered_sentences_for_guideline: Set[tuple[str, int]] = set()

        sentences = split_sentences_with_offsets(content_text)

        for guideline in guidelines:
            # 1. Prohibited Phrases Check
            prohibited_list = guideline.prohibited_phrases or []
            if isinstance(prohibited_list, list):
                # Sort longest phrases first to favor specific matches over generic
                sorted_prohibited = sorted(
                    [p.strip() for p in prohibited_list if p and p.strip()],
                    key=len,
                    reverse=True
                )
                for phrase in sorted_prohibited:
                    pattern = compile_phrase_pattern(phrase)
                    for match in pattern.finditer(content_text):
                        m_start = match.start()
                        m_end = match.end()
                        matched_claim = content_text[m_start:m_end]

                        # Generate exact UTF-16 offsets
                        start_u16, end_u16 = match_to_utf16_offsets(content_text, m_start, m_end)

                        # Grounded suggested correction
                        suggested_corr = None
                        if guideline.required_phrases and len(guideline.required_phrases) > 0:
                            approved_alt = guideline.required_phrases[0]
                            suggested_corr = f"Replace with approved phrasing: '{approved_alt}'."
                        else:
                            suggested_corr = f"Remove '{matched_claim}' to comply with '{guideline.title}'."

                        findings.append(
                            EngineFinding(
                                claim_text=matched_claim,
                                verdict=FindingVerdict.CONTRADICTED,
                                lane=ReviewLane.LANE_1_DETERMINISTIC,
                                explanation=(
                                    f"Prohibited phrase '{matched_claim}' violates brand guideline "
                                    f"'{guideline.title}' (Rule: {guideline.rule_text})."
                                ),
                                suggested_correction=suggested_corr,
                                guideline_id=guideline.id,
                                guideline_title=guideline.title,
                                guideline_version=guideline.version,
                                confidence_score=1.0,
                                start_offset=start_u16,
                                end_offset=end_u16,
                            )
                        )

                        # Track sentence to avoid duplicate required-phrase violations on same span
                        for s_text, s_start, s_end in sentences:
                            if s_start <= m_start and m_end <= s_end:
                                covered_sentences_for_guideline.add((guideline.id, s_start))

            # 2. Required Phrases & Mandatory Qualifiers Check
            required_list = guideline.required_phrases or []
            if isinstance(required_list, list) and len(required_list) > 0:
                relevance_keywords = extract_relevance_keywords(guideline)
                if relevance_keywords:
                    # Check if any sentence is relevant to this guideline topic
                    for s_text, s_start, s_end in sentences:
                        # Skip if already flagged for prohibited phrase under this guideline
                        if (guideline.id, s_start) in covered_sentences_for_guideline:
                            continue

                        s_words = set(re.findall(r"\b\w+\b", s_text.lower()))
                        # If the sentence discusses this guideline's subject matter
                        if relevance_keywords.intersection(s_words):
                            # Check whether ANY of the required phrases are present
                            has_required = any(
                                req_phrase.strip().lower() in s_text.lower()
                                for req_phrase in required_list
                                if req_phrase and req_phrase.strip()
                            )

                            if not has_required:
                                start_u16, end_u16 = match_to_utf16_offsets(content_text, s_start, s_end)
                                primary_req = required_list[0].strip()
                                findings.append(
                                    EngineFinding(
                                        claim_text=s_text,
                                        verdict=FindingVerdict.CONTRADICTED,
                                        lane=ReviewLane.LANE_1_DETERMINISTIC,
                                        explanation=(
                                            f"Content discusses topic '{guideline.title}' but omits mandatory "
                                            f"required phrase '{primary_req}'. Rule: {guideline.rule_text}"
                                        ),
                                        suggested_correction=f"Add mandatory qualifier or phrasing: '{primary_req}'.",
                                        guideline_id=guideline.id,
                                        guideline_title=guideline.title,
                                        guideline_version=guideline.version,
                                        confidence_score=1.0,
                                        start_offset=start_u16,
                                        end_offset=end_u16,
                                    )
                                )

        # Sort findings by start offset for deterministic, orderly output
        findings.sort(key=lambda f: (f.start_offset if f.start_offset is not None else -1))
        return findings
