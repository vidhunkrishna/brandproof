"""
Three-Lane Review Orchestrator for BrandProof.

Orchestrates the entire review lifecycle by integrating:
- Lane 1: Deterministic guideline checks (prohibited/required phrases)
- Lane 2: Grounded fact verification (numeric bounds, units, qualifiers, validity dates)
- Lane 3: Advisory AI claim extraction and analysis (with deterministic fallback)

Key invariants:
- Zero evidence assignment by AI: only server-side databases assign fact_id and guideline_id.
- Overlapping findings are deduplicated without discarding important evidence.
- Verdict precedence applied at individual claim level: CONTRADICTED > OUTDATED > CORRECT > UNSUPPORTED > UNVERIFIABLE.
- Overall revision verdict computed separately.
- Claims NEVER marked CORRECT without approved registry evidence.
- Preserves exact UTF-16 code-unit offsets across all lanes.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.enums import FindingVerdict, ReviewLane
from app.review_engine.models import EngineFinding
from app.review_engine.deterministic import DeterministicReviewEngine
from app.review_engine.fact_checker import GroundedFactChecker
from app.review_engine.ai_analyzer import AdvisoryAIAnalyzer
from app.review_engine.ai_provider import BaseAIProvider

logger = logging.getLogger("brandproof.orchestrator")


@dataclass
class ReviewResult:
    overall_verdict: str
    content_text: str
    findings: List[EngineFinding]
    is_fallback: bool
    total_findings: int
    correct_claims: int
    contradicted_claims: int
    outdated_claims: int
    unsupported_claims: int
    unverifiable_claims: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict,
            "content_text": self.content_text,
            "findings": [f.to_dict() for f in self.findings],
            "is_fallback": self.is_fallback,
            "total_findings": self.total_findings,
            "correct_claims": self.correct_claims,
            "contradicted_claims": self.contradicted_claims,
            "outdated_claims": self.outdated_claims,
            "unsupported_claims": self.unsupported_claims,
            "unverifiable_claims": self.unverifiable_claims,
        }


def check_spans_overlap(s1: Optional[int], e1: Optional[int], s2: Optional[int], e2: Optional[int]) -> bool:
    """Check if two offset intervals [s1, e1) and [s2, e2) overlap."""
    if s1 is None or e1 is None or s2 is None or e2 is None:
        return False
    return max(s1, s2) < min(e1, e2)


class ReviewOrchestrator:
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        self.ai_analyzer = AdvisoryAIAnalyzer(provider=ai_provider)

    def run_review(
        self,
        db: Session,
        organization_id: str,
        content_text: str,
    ) -> ReviewResult:
        """
        Execute three-lane governance review against content text.
        """
        if not content_text or not content_text.strip():
            return ReviewResult(
                overall_verdict="NEEDS_REVIEW",
                content_text=content_text or "",
                findings=[],
                is_fallback=False,
                total_findings=0,
                correct_claims=0,
                contradicted_claims=0,
                outdated_claims=0,
                unsupported_claims=0,
                unverifiable_claims=0,
            )

        # -------------------------------------------------------------
        # 1. LANE 1: Deterministic Guideline Engine
        # -------------------------------------------------------------
        lane1_findings = DeterministicReviewEngine.evaluate(
            db=db,
            organization_id=organization_id,
            content_text=content_text,
        )
        # -------------------------------------------------------------
        # 2. LANE 2: Grounded Fact Verification Engine
        # -------------------------------------------------------------
        lane2_findings = GroundedFactChecker.evaluate(
            db=db,
            organization_id=organization_id,
            content_text=content_text,
        )
        # -------------------------------------------------------------
        # 3. LANE 3: Advisory AI Extraction & Analysis
        # -------------------------------------------------------------
        lane3_findings, is_fallback = self.ai_analyzer.analyze(content_text=content_text)

        # -------------------------------------------------------------
        # 4. INTELLIGENT DEDUPLICATION & VERDICT PRECEDENCE
        # -------------------------------------------------------------
        # Grounded findings (Lane 1 & 2) have verified database backing.
        # Lane 1 findings are guideline rules (e.g. prohibited phrases).
        # Lane 2 findings are fact checks (e.g. numeric boundaries).
        # Both represent distinct, valuable evidence and are preserved.
        combined_grounded: List[EngineFinding] = list(lane1_findings) + list(lane2_findings)

        # Deduplicate grounded findings:
        # If a finding is already CONTRADICTED, OUTDATED, or CORRECT, any generic
        # UNSUPPORTED or UNVERIFIABLE finding overlapping the exact same span is superseded and dropped.
        grounded_deduped: List[EngineFinding] = []
        for g in combined_grounded:
            if g.verdict in (FindingVerdict.UNVERIFIABLE, FindingVerdict.UNSUPPORTED):
                has_better = any(
                    other.verdict in (FindingVerdict.CONTRADICTED, FindingVerdict.CORRECT, FindingVerdict.OUTDATED)
                    and check_spans_overlap(g.start_offset, g.end_offset, other.start_offset, other.end_offset)
                    for other in combined_grounded
                    if other is not g
                )
                if has_better:
                    continue
            grounded_deduped.append(g)

        final_findings: List[EngineFinding] = list(grounded_deduped)

        # Integrate Lane 3 (Advisory):
        # If an advisory claim overlaps with a verified claim (from Lane 1 or Lane 2),
        # the grounded evidence takes precedence and the unverified advisory duplicate is discarded.
        # If an advisory claim is NOT covered by Lane 1 or Lane 2, it is preserved as UNSUPPORTED / UNVERIFIABLE.
        for l3_finding in lane3_findings:
            overlaps_grounded = any(
                check_spans_overlap(
                    l3_finding.start_offset,
                    l3_finding.end_offset,
                    g_finding.start_offset,
                    g_finding.end_offset,
                )
                for g_finding in grounded_deduped
            )

            if not overlaps_grounded:
                # Keep advisory finding for unevidenced claim
                final_findings.append(l3_finding)

        # Sort findings by start_offset
        final_findings.sort(key=lambda f: (f.start_offset if f.start_offset is not None else -1))

        # -------------------------------------------------------------
        # 5. COMPUTE CLAIM COUNTS & OVERALL REVISION VERDICT
        # -------------------------------------------------------------
        correct_count = sum(1 for f in final_findings if f.verdict == FindingVerdict.CORRECT)
        contradicted_count = sum(1 for f in final_findings if f.verdict == FindingVerdict.CONTRADICTED)
        outdated_count = sum(1 for f in final_findings if f.verdict == FindingVerdict.OUTDATED)
        unsupported_count = sum(1 for f in final_findings if f.verdict == FindingVerdict.UNSUPPORTED)
        unverifiable_count = sum(1 for f in final_findings if f.verdict == FindingVerdict.UNVERIFIABLE)
        total_findings = len(final_findings)

        # Precedence for overall revision verdict:
        # CONTRADICTED > OUTDATED > MIXED > CORRECT > UNSUPPORTED > UNVERIFIABLE > NEEDS_REVIEW
        if contradicted_count > 0:
            overall_verdict = "CONTRADICTED"
        elif outdated_count > 0:
            overall_verdict = "OUTDATED"
        elif (unsupported_count > 0 or unverifiable_count > 0) and correct_count > 0:
            overall_verdict = "MIXED"
        elif correct_count > 0 and (unsupported_count == 0 and unverifiable_count == 0):
            overall_verdict = "CORRECT"
        elif unsupported_count > 0:
            overall_verdict = "UNSUPPORTED"
        elif unverifiable_count > 0:
            overall_verdict = "UNVERIFIABLE"
        else:
            overall_verdict = "NEEDS_REVIEW"

        return ReviewResult(
            overall_verdict=overall_verdict,
            content_text=content_text,
            findings=final_findings,
            is_fallback=is_fallback,
            total_findings=total_findings,
            correct_claims=correct_count,
            contradicted_claims=contradicted_count,
            outdated_claims=outdated_count,
            unsupported_claims=unsupported_count,
            unverifiable_claims=unverifiable_count,
        )
