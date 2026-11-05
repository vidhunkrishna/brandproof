"""
Lane 2 — Grounded Fact Verification Engine for BrandProof.

Evaluates marketing content strictly against organization-scoped approved facts:
- Compares claims against approved facts using deterministic numeric and qualifier checks.
- Safely parses numeric values and normalizes units.
- Evaluates numeric operators (<=, >=, ==).
- Validates mandatory required qualifiers.
- Checks validity dates and identifies expired facts (OUTDATED).
- Detects claims tied to superseded facts (OUTDATED).
- Returns UNVERIFIABLE for claims that cannot be reliably mapped to evidence.
- Never marks unevidenced claims as CORRECT or CONTRADICTED.
- Employs UTF-16 code-unit offsets [start_offset, end_offset) for exact JavaScript substring compatibility.
- Operates deterministically with zero LLM dependency.
"""
import re
from typing import List, Optional, Set, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.knowledge import ApprovedFact
from app.models.enums import FactStatus, FindingVerdict, ReviewLane
from app.review_engine.models import EngineFinding
from app.review_engine.deterministic import split_sentences_with_offsets
from app.core.text_utils import match_to_utf16_offsets


# Unit normalization map
UNIT_SYNONYMS = {
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "year": "years",
    "years": "years",
    "yr": "years",
    "yrs": "years",
    "month": "months",
    "months": "months",
    "day": "days",
    "days": "days",
    "hour": "hours",
    "hours": "hours",
    "hr": "hours",
    "hrs": "hours",
    "minute": "minutes",
    "minutes": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "second": "seconds",
    "seconds": "seconds",
    "sec": "seconds",
    "secs": "seconds",
    "ms": "ms",
    "millisecond": "ms",
    "milliseconds": "ms",
    "kwh": "kwh",
    "kw": "kw",
    "w": "w",
    "watt": "w",
    "watts": "w",
    "gb": "gb",
    "tb": "tb",
    "mbps": "mbps",
    "gbps": "gbps",
}

# Regex to find numeric values and their associated units
NUMERIC_REGEX = re.compile(
    r"(?<!#)\b(\d+(?:\.\d+)?)\s*(%|percent|percentage|years?|yrs?|months?|days?|hours?|hrs?|mins?|minutes?|secs?|seconds?|ms|milliseconds?|kwh|kw|w|watts?|gb|tb|mbps|gbps)?\b",
    re.IGNORECASE
)

# Marketing claim indicators that suggest an empirical statement is being made
MARKETING_CLAIM_INDICATORS = [
    "save", "saving", "savings", "guarantee", "guaranteed", "warranty",
    "uptime", "accuracy", "leader", "#1", "first", "certified", "proven",
    "efficiency", "lifespan", "reduction", "fastest", "best", "lifetime"
]

SUPERLATIVE_INDICATORS = [
    "#1", "number one", "first", "best", "fastest", "leading", "leader",
    "undisputed", "revolutionary", "world-class", "ultimate", "unrivaled", "unmatched"
]


def normalize_unit(unit_str: Optional[str]) -> Optional[str]:
    """Normalize common unit variants into standard canonical forms."""
    if not unit_str:
        return None
    cleaned = unit_str.strip().lower()
    return UNIT_SYNONYMS.get(cleaned, cleaned)


def extract_numeric_and_unit(sentence: str) -> List[Tuple[float, Optional[str], int, int]]:
    """
    Extract numbers, normalized units, and codepoint positions from a sentence.
    Returns list of (numeric_value, normalized_unit, start_idx, end_idx).
    """
    results = []
    for m in NUMERIC_REGEX.finditer(sentence):
        val_str = m.group(1)
        unit_raw = m.group(2)
        try:
            val = float(val_str)
            norm_unit = normalize_unit(unit_raw)
            results.append((val, norm_unit, m.start(), m.end()))
        except ValueError:
            continue
    return results


def extract_fact_keywords(fact: ApprovedFact) -> Set[str]:
    """
    Extract core semantic topic keywords from an ApprovedFact.
    """
    keywords: Set[str] = set()

    # Fact name words
    if fact.fact_name:
        for word in re.findall(r"\b\w{3,}\b", fact.fact_name.lower()):
            if word not in ("the", "and", "for", "with", "all", "our", "fact"):
                keywords.add(word)

    # Category words
    if fact.category and fact.category.lower() not in ("general", "misc"):
        for word in re.findall(r"\b\w{3,}\b", fact.category.lower()):
            keywords.add(word)

    # Synonyms / topic stems
    expanded = set(keywords)
    for kw in keywords:
        if kw.startswith("saving") or kw.startswith("save"):
            expanded.update(["save", "saving", "savings", "reduction"])
        elif kw.startswith("warrant"):
            expanded.update(["warranty", "guarantee", "coverage"])
        elif kw.startswith("energi") or kw.startswith("energy"):
            expanded.update(["energy", "power", "efficiency"])
        elif kw.startswith("life"):
            expanded.update(["lifespan", "lasting", "hours"])

    return expanded


class GroundedFactChecker:
    @staticmethod
    def get_evaluable_facts(db: Session, organization_id: str) -> List[ApprovedFact]:
        """
        Retrieve organization-scoped approved and superseded facts.
        Draft and pending facts (PENDING_APPROVAL) are strictly excluded from evidence.
        """
        return (
            db.query(ApprovedFact)
            .filter(
                ApprovedFact.organization_id == organization_id,
                ApprovedFact.status.in_([FactStatus.APPROVED, FactStatus.SUPERSEDED]),
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
        Execute Lane 2 grounded fact verification against database facts.
        """
        if not content_text or not content_text.strip():
            return []

        evaluable_facts = cls.get_evaluable_facts(db, organization_id)
        findings: List[EngineFinding] = []
        sentences = split_sentences_with_offsets(content_text)
        evaluated_sentences: Set[int] = set()

        for s_text, s_start, s_end in sentences:
            sentence_lower = s_text.lower()
            numerics = extract_numeric_and_unit(s_text)
            sentence_words = set(re.findall(r"\b\w+\b", sentence_lower))

            # Score candidate facts to find the most specific match
            best_fact = None
            best_numeric = None
            highest_score = 0.0

            for fact in evaluable_facts:
                fact_kws = extract_fact_keywords(fact)
                norm_fact_unit = normalize_unit(fact.unit)

                # Check topic relevance
                overlap = fact_kws.intersection(sentence_words)
                if not overlap:
                    continue

                # Specific fact name match count
                name_words = [w for w in re.findall(r"\b\w{3,}\b", fact.fact_name.lower()) if w not in ("the", "and", "for", "with", "all", "our", "fact")]
                name_overlap_count = len([w for w in name_words if w in sentence_words])
                name_ratio = name_overlap_count / max(len(name_words), 1)

                matched_num = None
                unit_compat = False
                val_exact = False

                if numerics and norm_fact_unit:
                    for num_val, num_unit, n_start, n_end in numerics:
                        if num_unit == norm_fact_unit or (num_unit is None and norm_fact_unit == "%" and "%" in s_text):
                            matched_num = (num_val, norm_fact_unit)
                            unit_compat = True
                            if fact.numeric_value is not None and abs(num_val - fact.numeric_value) < 1e-5:
                                val_exact = True
                            break
                    if not unit_compat:
                        continue
                elif not numerics:
                    if "lifetime" in sentence_words and norm_fact_unit == "years":
                        unit_compat = True
                    else:
                        continue
                else:
                    continue

                # Ranking score:
                # 1. Specific name overlap ratio & count
                # 2. Exact value match (crucial to tie claim to superseded fact vs active fact)
                # 3. Keyword overlap
                # 4. Tie-breaker preference for APPROVED over SUPERSEDED
                fact_score = (name_ratio * 15.0) + (name_overlap_count * 5.0) + (len(overlap) * 2.0)
                if val_exact:
                    fact_score += 10.0
                if fact.status == FactStatus.APPROVED:
                    fact_score += 1.0

                if fact_score > highest_score:
                    highest_score = fact_score
                    best_fact = fact
                    best_numeric = matched_num

            matched_fact = best_fact
            matched_numeric = best_numeric

            if matched_fact is not None:
                start_u16, end_u16 = match_to_utf16_offsets(content_text, s_start, s_end)
                evaluated_sentences.add(s_start)

                # Case 1: Non-numeric qualitative claim where numeric fact exists (e.g., "Lifetime warranty")
                # Rule: Do not infer that "lifetime" equals a numeric warranty duration using numeric parsing.
                # Return UNVERIFIABLE.
                if matched_numeric is None:
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.UNVERIFIABLE,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=(
                                f"Claim makes qualitative statement '{s_text}' which cannot be verified "
                                f"against approved numeric fact '{matched_fact.fact_name}' ({matched_fact.approved_value}) "
                                f"without deterministic guideline rules."
                            ),
                            suggested_correction=f"Use approved numeric specification: '{matched_fact.approved_value}'.",
                            fact_id=matched_fact.id,
                            fact_name=matched_fact.fact_name,
                            fact_version=matched_fact.version,
                            fact_approved_value=matched_fact.approved_value,
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )
                    continue

                claim_val, claim_unit = matched_numeric

                # Case 2: Expired Fact
                now_utc = datetime.now(timezone.utc)
                if matched_fact.valid_until is not None:
                    f_until = matched_fact.valid_until
                    if f_until.tzinfo is None:
                        f_until = f_until.replace(tzinfo=timezone.utc)
                    if f_until < now_utc:
                        findings.append(
                            EngineFinding(
                                claim_text=s_text,
                                verdict=FindingVerdict.OUTDATED,
                                lane=ReviewLane.LANE_2_GROUNDED_FACT,
                                explanation=(
                                    f"Claim is grounded in fact '{matched_fact.fact_name}' which expired on "
                                    f"{f_until.strftime('%Y-%m-%d')}."
                                ),
                                suggested_correction="Renew or update expired evidence before approval.",
                                fact_id=matched_fact.id,
                                fact_name=matched_fact.fact_name,
                                fact_version=matched_fact.version,
                                fact_approved_value=matched_fact.approved_value,
                                start_offset=start_u16,
                                end_offset=end_u16,
                            )
                        )
                        continue

                # Case 3: Superseded Fact
                if matched_fact.status == FactStatus.SUPERSEDED:
                    # Look up newest approved replacement
                    latest_fact = (
                        db.query(ApprovedFact)
                        .filter(
                            ApprovedFact.organization_id == organization_id,
                            ApprovedFact.fact_name.ilike(matched_fact.fact_name),
                            ApprovedFact.status == FactStatus.APPROVED,
                        )
                        .order_by(ApprovedFact.version.desc())
                        .first()
                    )
                    corr_text = (
                        f"Update claim to current approved value: '{latest_fact.approved_value}'."
                        if latest_fact else None
                    )
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.OUTDATED,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=(
                                f"Claim references superseded fact '{matched_fact.fact_name}' "
                                f"(v{matched_fact.version}: {matched_fact.approved_value}). A newer approved version exists."
                            ),
                            suggested_correction=corr_text,
                            fact_id=matched_fact.id,
                            fact_name=matched_fact.fact_name,
                            fact_version=matched_fact.version,
                            fact_approved_value=matched_fact.approved_value,
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )
                    continue

                # Case 4: Numeric Operator Evaluation
                target_val = matched_fact.numeric_value
                operator = matched_fact.numeric_operator or "<="
                is_contradicted = False
                op_explanation = ""

                if target_val is not None:
                    if operator == "<=":
                        if claim_val > target_val:
                            is_contradicted = True
                            op_explanation = (
                                f"Claimed value {claim_val}{matched_fact.unit or ''} exceeds approved limit of "
                                f"{target_val}{matched_fact.unit or ''} for '{matched_fact.fact_name}' (operator: <=)."
                            )
                    elif operator == ">=":
                        if claim_val < target_val:
                            is_contradicted = True
                            op_explanation = (
                                f"Claimed value {claim_val}{matched_fact.unit or ''} falls below approved minimum of "
                                f"{target_val}{matched_fact.unit or ''} for '{matched_fact.fact_name}' (operator: >=)."
                            )
                    elif operator in ("==", "="):
                        if abs(claim_val - target_val) > 1e-5:
                            is_contradicted = True
                            op_explanation = (
                                f"Claimed value {claim_val}{matched_fact.unit or ''} does not match approved exact value of "
                                f"{target_val}{matched_fact.unit or ''} for '{matched_fact.fact_name}'."
                            )

                if is_contradicted:
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.CONTRADICTED,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=op_explanation,
                            suggested_correction=f"Correct claim to approved specification: '{matched_fact.approved_value}'.",
                            fact_id=matched_fact.id,
                            fact_name=matched_fact.fact_name,
                            fact_version=matched_fact.version,
                            fact_approved_value=matched_fact.approved_value,
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )
                    continue

                # Case 5: Required Qualifiers Check
                # A missing qualifier can be a contradiction only when the approved fact explicitly
                # requires it and the claim clearly refers to that fact.
                missing_qualifier = None
                if matched_fact.required_qualifiers:
                    for req_q in matched_fact.required_qualifiers:
                        req_q_clean = req_q.strip().lower()
                        # Qualifier must appear in the claim sentence or surrounding text
                        if req_q_clean not in sentence_lower and req_q_clean not in content_text.lower():
                            missing_qualifier = req_q.strip()
                            break

                if missing_qualifier:
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.CONTRADICTED,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=(
                                f"Claim matches numeric value for '{matched_fact.fact_name}' but omits mandatory "
                                f"qualifier: '{missing_qualifier}'."
                            ),
                            suggested_correction=f"Add mandatory qualifier '{missing_qualifier}' to substantiate claim.",
                            fact_id=matched_fact.id,
                            fact_name=matched_fact.fact_name,
                            fact_version=matched_fact.version,
                            fact_approved_value=matched_fact.approved_value,
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )
                    continue

                # Case 6: Fully Verified Fact (CORRECT)
                findings.append(
                    EngineFinding(
                        claim_text=s_text,
                        verdict=FindingVerdict.CORRECT,
                        lane=ReviewLane.LANE_2_GROUNDED_FACT,
                        explanation=(
                            f"Claim verified against approved fact '{matched_fact.fact_name}' "
                            f"(v{matched_fact.version}: {matched_fact.approved_value})."
                        ),
                        suggested_correction=None,
                        fact_id=matched_fact.id,
                        fact_name=matched_fact.fact_name,
                        fact_version=matched_fact.version,
                        fact_approved_value=matched_fact.approved_value,
                        start_offset=start_u16,
                        end_offset=end_u16,
                    )
                )

            else:
                # Evaluate sentences without a matching approved fact:
                # 1. Clearly identifiable factual claim without approved evidence -> UNSUPPORTED
                # 2. Ambiguous or unmatchable claim -> UNVERIFIABLE
                has_indicator = any(ind in sentence_lower for ind in MARKETING_CLAIM_INDICATORS)
                has_superlative = any(sup in sentence_lower for sup in SUPERLATIVE_INDICATORS)
                has_unit_numeric = any(unit is not None for _, unit, _, _ in numerics)

                if has_unit_numeric or (has_indicator and numerics):
                    start_u16, end_u16 = match_to_utf16_offsets(content_text, s_start, s_end)
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.UNSUPPORTED,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=(
                                f"Empirical claim '{s_text}' has no corresponding approved fact in the brand registry."
                            ),
                            suggested_correction="Register and approve evidence in the brand fact registry before publishing.",
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )
                elif has_indicator or has_superlative:
                    start_u16, end_u16 = match_to_utf16_offsets(content_text, s_start, s_end)
                    findings.append(
                        EngineFinding(
                            claim_text=s_text,
                            verdict=FindingVerdict.UNVERIFIABLE,
                            lane=ReviewLane.LANE_2_GROUNDED_FACT,
                            explanation=(
                                f"Claim '{s_text}' is ambiguous or unmatchable and cannot be reliably evaluated against registry facts."
                            ),
                            suggested_correction="Provide objective, verifiable metrics or reference an approved guideline.",
                            start_offset=start_u16,
                            end_offset=end_u16,
                        )
                    )

        findings.sort(key=lambda f: (f.start_offset if f.start_offset is not None else -1))
        return findings
