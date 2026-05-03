import type { UrlMetaFeatureHighlight } from "@lib/types";

/** Per-label thresholds on 0–1 scores; higher = more suspicious. Unknown labels use default. */
const URL_META_THRESHOLDS: Record<string, number> = {
  "path ratio": 0.35,
  "tld tier": 0.4,
  entropy: 0.45,
  "dot count": 0.35,
  "digit ratio": 0.35,
  "special chars": 0.5,
  "subdomain flag": 0.5,
  "path depth": 0.45,
};

const DEFAULT_THRESHOLD = 0.45;

const EXPLANATIONS: Record<string, string> = {
  "path ratio":
    "The path portion of the URL is unusually long or dominant compared with typical links.",
  "tld tier":
    "The top-level domain category is often associated with higher-risk or disposable registrations.",
  entropy:
    "High randomness in the hostname or path—common in auto-generated or obfuscated links.",
  "dot count":
    "Many dot-separated segments can indicate long chains, redirects, or confusing structure.",
  "digit ratio":
    "An unusually high share of digits may appear in shortened or machine-like URLs.",
  "special chars":
    "Many non-alphanumeric symbols can be used to mimic trusted sites or bypass filters.",
  "subdomain flag":
    "Unusual subdomain depth or patterns can hide who really controls the site.",
  "path depth":
    "Deep folder paths may bury the real destination or mimic legitimate portals.",
};

function normalizeLabel(label: unknown): string | null {
  if (typeof label !== "string" || !label.trim()) return null;
  return label.trim().toLowerCase();
}

function toFiniteScore(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function thresholdForLabel(normalized: string): number {
  return URL_META_THRESHOLDS[normalized] ?? DEFAULT_THRESHOLD;
}

function severityForScore(score: number): UrlMetaFeatureHighlight["severity"] {
  if (score >= 0.65) return "high";
  if (score >= 0.45) return "medium";
  return "low";
}

function explanationForLabel(displayLabel: string, normalized: string): string {
  return (
    EXPLANATIONS[normalized] ??
    `This factor (${displayLabel}) exceeds the usual safe range for this check.`
  );
}

/**
 * Picks up to `maxItems` URL structure signals that exceed per-feature thresholds.
 * Scores are independent 0–1 dimensions; 0 means “no concern” for that dimension.
 */
export function buildUrlMetaHighlights(
  metaLabels: unknown,
  metaVector: unknown,
  options?: { maxItems?: number },
): UrlMetaFeatureHighlight[] {
  const maxItems = options?.maxItems ?? 3;
  if (!Array.isArray(metaLabels) || !Array.isArray(metaVector)) return [];

  const n = Math.min(metaLabels.length, metaVector.length);
  const candidates: UrlMetaFeatureHighlight[] = [];

  for (let i = 0; i < n; i++) {
    const normalized = normalizeLabel(metaLabels[i]);
    if (!normalized) continue;
    const score = toFiniteScore(metaVector[i]);
    if (score === null || score <= 0) continue;

    const threshold = thresholdForLabel(normalized);
    if (score < threshold) continue;

    const displayLabel =
      typeof metaLabels[i] === "string" && metaLabels[i].trim()
        ? metaLabels[i].trim()
        : normalized;

    candidates.push({
      label: displayLabel,
      score,
      severity: severityForScore(score),
      explanation: explanationForLabel(displayLabel, normalized),
    });
  }

  candidates.sort((a, b) => b.score - a.score);
  return candidates.slice(0, maxItems);
}
