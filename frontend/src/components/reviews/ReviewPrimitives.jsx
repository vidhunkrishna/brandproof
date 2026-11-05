import React from 'react';

export const VERDICT_META = {
  CORRECT: {
    label: 'Correct',
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    highlight: 'bg-emerald-100 text-emerald-950 decoration-emerald-500',
  },
  CONTRADICTED: {
    label: 'Contradicted',
    badge: 'bg-rose-50 text-rose-800 border-rose-200',
    highlight: 'bg-rose-100 text-rose-950 decoration-rose-500',
  },
  OUTDATED: {
    label: 'Outdated',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    highlight: 'bg-amber-100 text-amber-950 decoration-amber-500',
  },
  UNSUPPORTED: {
    label: 'Unsupported',
    badge: 'bg-purple-50 text-purple-800 border-purple-200',
    highlight: 'bg-purple-100 text-purple-950 decoration-purple-500',
  },
  UNVERIFIABLE: {
    label: 'Unverifiable',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    highlight: 'bg-slate-200 text-slate-950 decoration-slate-500',
  },
  MIXED: {
    label: 'Mixed',
    badge: 'bg-blue-50 text-blue-800 border-blue-200',
    highlight: 'bg-blue-100 text-blue-950 decoration-blue-500',
  },
  NEEDS_REVIEW: {
    label: 'Needs review',
    badge: 'bg-neutral-100 text-neutral-700 border-neutral-200',
    highlight: 'bg-neutral-200 text-neutral-950 decoration-neutral-500',
  },
};

const FALLBACK_META = {
  label: 'Unknown',
  badge: 'bg-slate-100 text-slate-700 border-slate-200',
  highlight: 'bg-slate-200 text-slate-950 decoration-slate-500',
};

export function verdictMeta(verdict) {
  return VERDICT_META[verdict] || FALLBACK_META;
}

export function VerdictBadge({ verdict, className = '' }) {
  const meta = verdictMeta(verdict);
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${meta.badge} ${className}`}>
      {meta.label}
    </span>
  );
}

export function formatLane(lane) {
  const labels = {
    LANE_1_DETERMINISTIC: 'Guideline rules',
    LANE_2_GROUNDED_FACT: 'Approved facts',
    LANE_3_ADVISORY_AI: 'Advisory AI',
  };
  return labels[lane] || lane?.replaceAll('_', ' ') || 'Review lane unavailable';
}

export function countFindings(findings = []) {
  return findings.reduce(
    (counts, finding) => {
      if (Object.hasOwn(counts, finding.verdict)) counts[finding.verdict] += 1;
      return counts;
    },
    { CORRECT: 0, CONTRADICTED: 0, OUTDATED: 0, UNSUPPORTED: 0, UNVERIFIABLE: 0 }
  );
}

function priorityForVerdict(verdict) {
  return ['CONTRADICTED', 'OUTDATED', 'UNSUPPORTED', 'UNVERIFIABLE', 'CORRECT'].indexOf(verdict);
}

/**
 * Renders one pass over the original JavaScript string. API offsets are UTF-16
 * code units, so substring() preserves emoji and multilingual text exactly.
 */
export function HighlightedCopy({ text, findings = [] }) {
  const validFindings = findings.filter((finding) => (
    Number.isInteger(finding.start_offset)
    && Number.isInteger(finding.end_offset)
    && finding.start_offset >= 0
    && finding.end_offset > finding.start_offset
    && finding.end_offset <= text.length
  ));

  if (!validFindings.length) {
    return <>{text}</>;
  }

  const boundaries = [...new Set([
    0,
    text.length,
    ...validFindings.flatMap((finding) => [finding.start_offset, finding.end_offset]),
  ])].sort((a, b) => a - b);

  return boundaries.slice(0, -1).map((start, index) => {
    const end = boundaries[index + 1];
    const segment = text.substring(start, end);
    const active = validFindings
      .filter((finding) => finding.start_offset <= start && finding.end_offset >= end)
      .sort((a, b) => priorityForVerdict(a.verdict) - priorityForVerdict(b.verdict));

    if (!active.length) {
      return <React.Fragment key={`${start}-${end}`}>{segment}</React.Fragment>;
    }

    const primary = active[0];
    const descriptions = active.map((finding) => `${verdictMeta(finding.verdict).label}: ${finding.explanation}`);
    return (
      <mark
        key={`${start}-${end}`}
        title={descriptions.join('\n')}
        className={`rounded px-0.5 underline decoration-2 underline-offset-2 ${verdictMeta(primary.verdict).highlight}`}
      >
        {segment}
      </mark>
    );
  });
}

export function ReviewMode({ isFallback }) {
  if (isFallback === true) {
    return <span className="text-amber-700">Deterministic fallback</span>;
  }
  if (isFallback === false) {
    return <span className="text-blue-700">AI-assisted review</span>;
  }
  return <span className="text-slate-500">Mode was not retained for this historical revision</span>;
}
