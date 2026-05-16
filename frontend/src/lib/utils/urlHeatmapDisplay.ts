import type {
  UrlHeatmapFusionWeights,
  UrlHeatmapUiSignals,
  UrlTokenHeatmapEntry,
} from "@lib/types";

/** Matches backend `standardize_url` in `nlp_service.py` (lowercase, https, strip www). */
export function standardizeUrlForHeatmap(url: string): string {
  const trimmed = url.trim().toLowerCase();
  const noProto = trimmed.replace(/^https?:\/\//, "");
  const clean = noProto.replace(/^www\./, "");
  return `https://${clean}`;
}

function parseNumber(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

function clamp11(n: number): number {
  return Math.max(-1, Math.min(1, n));
}

function parseUiSignals(
  raw: unknown,
  legacyLexical: boolean,
): UrlHeatmapUiSignals | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const u = raw as Record<string, unknown>;
  const nx = parseNumber(u.norm_xgb, NaN);
  const ns = parseNumber(u.norm_semantic, NaN);
  let il = typeof u.is_lexical === "boolean" ? (u.is_lexical ? 1 : 0) : NaN;
  if (!Number.isFinite(il)) {
    il = u.is_lexical !== undefined ? parseNumber(u.is_lexical, NaN) : NaN;
  }
  if (!Number.isFinite(il) && u.is_lexical_match !== undefined) {
    il = legacyLexical || Boolean(u.is_lexical_match) ? 1 : 0;
  }
  if (!Number.isFinite(nx) || !Number.isFinite(ns) || !Number.isFinite(il)) {
    return undefined;
  }
  return {
    norm_xgb: clamp01(nx),
    norm_semantic: clamp01(ns),
    is_lexical: clamp01(il),
  };
}

/** Normalizes raw API `explainability.token_heatmap` items. */
export function parseUrlTokenHeatmap(raw: unknown): UrlTokenHeatmapEntry[] {
  if (!Array.isArray(raw)) return [];
  const out: UrlTokenHeatmapEntry[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const o = item as Record<string, unknown>;
    const start = parseNumber(o.start_char, NaN);
    const end = parseNumber(o.end_char, NaN);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) {
      continue;
    }
    const legacyLexical = Boolean(o.is_lexical_match);
    const ui_signals = parseUiSignals(o.ui_signals, legacyLexical);
    const row: UrlTokenHeatmapEntry = {
      token_text: typeof o.token_text === "string" ? o.token_text : "",
      start_char: start,
      end_char: end,
      xgb_predictive_delta: parseNumber(o.xgb_predictive_delta, 0),
      semantic_similarity: parseNumber(o.semantic_similarity, 0),
      is_lexical_match: legacyLexical,
    };
    if (ui_signals) row.ui_signals = ui_signals;
    out.push(row);
  }
  return out.sort((a, b) => a.start_char - b.start_char);
}

/** Text branch: semantic gets more retrieval weight on XGB; URL the opposite (spec). */
export type HeatmapBranchMode = "text" | "url";

/** Fused intensity in ~[0,1] matching backend/UI contract when signals + weights exist. */
export function computeUnifiedSegmentIntensity(
  signals: UrlHeatmapUiSignals,
  fusion: UrlHeatmapFusionWeights,
  mode: HeatmapBranchMode,
): number {
  const wx = fusion.effective_xgb_weight;
  const wd = fusion.effective_db_weight;
  const x = mode === "text" ? 0.7 : 0.3;
  const y = mode === "text" ? 0.3 : 0.7;
  const raw =
    signals.norm_xgb * wx +
    signals.norm_semantic * wd * x +
    signals.is_lexical * wd * y;
  return clamp01(raw);
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpRgb(
  c0: readonly [number, number, number],
  c1: readonly [number, number, number],
  t: number,
): [number, number, number] {
  const u = clamp01(t);
  return [
    Math.round(lerp(c0[0], c1[0], u)),
    Math.round(lerp(c0[1], c1[1], u)),
    Math.round(lerp(c0[2], c1[2], u)),
  ];
}

/** Multi-stop lerp along t∈[0,1]; positions must be ascending. */
function sampleColorStops(
  t: number,
  stops: Array<{ pos: number; rgb: [number, number, number] }>,
): [number, number, number] {
  const x = clamp01(t);
  if (stops.length === 0) return [226, 232, 240];
  if (x <= stops[0].pos) return [...stops[0].rgb] as [number, number, number];
  if (x >= stops[stops.length - 1].pos)
    return [...stops[stops.length - 1].rgb] as [number, number, number];
  for (let i = 0; i < stops.length - 1; i++) {
    const a = stops[i];
    const b = stops[i + 1];
    if (x >= a.pos && x <= b.pos) {
      const w = (x - a.pos) / (b.pos - a.pos);
      const u = w * w * (3 - 2 * w);
      return lerpRgb(a.rgb, b.rgb, u);
    }
  }
  return [...stops[stops.length - 1].rgb] as [number, number, number];
}

/** Amber / yellow → red ramp (#FAE792 family → red-600). */
const AMBER_HEATMAP_STOPS: Array<{
  pos: number;
  rgb: [number, number, number];
}> = [
  { pos: 0.0, rgb: [255, 251, 235] },
  { pos: 0.22, rgb: [253, 230, 138] },
  { pos: 0.45, rgb: [250, 231, 146] }, // #FAE792
  { pos: 0.62, rgb: [251, 191, 36] },
  { pos: 0.8, rgb: [251, 146, 60] },
  { pos: 1.0, rgb: [220, 38, 38] },
];

function amberHeatmapStyles(u: number): {
  backgroundColor: string;
  color?: string;
} {
  const t = clamp01(u);
  const rgb = sampleColorStops(t, AMBER_HEATMAP_STOPS);
  const lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
  const color = t < 0.58 ? "#78350f" : lum > 0.45 ? "#ffffff" : "#7f1d1d";
  return {
    backgroundColor: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
    color,
  };
}

const NEUTRAL_SPAN_STYLE: { backgroundColor: string; color?: string } = {
  backgroundColor: "transparent",
  color: undefined,
};

/** Relative ramp below → no fill (low tier). */
const HEATMAP_LOW_CUTOFF = 1 / 3;
/** At or above → red/orange band (high tier); between low and high → amber/yellow only. */
const HEATMAP_HIGH_CUTOFF = 0.98;

/** Maps display ramp: low = none, mid = amber/yellow, high = orange → red. */
function intensityToUnifiedHeatmapStyles(displayRamp: number): {
  backgroundColor: string;
  color?: string;
} {
  const s = clamp01(displayRamp);
  if (s < HEATMAP_LOW_CUTOFF - 1e-6) {
    return NEUTRAL_SPAN_STYLE;
  }

  if (s < HEATMAP_HIGH_CUTOFF - 1e-6) {
    const t =
      (s - HEATMAP_LOW_CUTOFF) / (HEATMAP_HIGH_CUTOFF - HEATMAP_LOW_CUTOFF);
    const u = Math.pow(clamp01(t), 0.55) * 0.55;
    return amberHeatmapStyles(u);
  }

  const t = (s - HEATMAP_HIGH_CUTOFF) / (1 - HEATMAP_HIGH_CUTOFF);
  const u = 0.55 + Math.pow(clamp01(t), 0.5) * 0.45;
  return amberHeatmapStyles(u);
}

/** Max fused score across tokens (for per-URL contrast stretch). */
export function maxFusedScoreInBatch(
  tokens: UrlTokenHeatmapEntry[],
  fusion: UrlHeatmapFusionWeights,
  mode: HeatmapBranchMode = "url",
): number {
  let max = 0;
  for (const t of tokens) {
    if (!t.ui_signals) continue;
    const s = computeUnifiedSegmentIntensity(t.ui_signals, fusion, mode);
    if (s > max) max = s;
  }
  return max;
}

/** Stretch score against URL max so low/high segments separate visually. */
export function fusedScoreToDisplayRamp(
  score: number,
  batchMaxFused: number,
): number {
  const s = clamp01(score);
  const cap = Math.max(batchMaxFused, 1e-6);
  return clamp01(s / cap);
}

export function percentileSorted(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  if (sorted.length === 1) return sorted[0];
  const idx = (sorted.length - 1) * p;
  const lo = Math.min(Math.floor(idx), sorted.length - 1);
  const hi = Math.min(Math.ceil(idx), sorted.length - 1);
  if (lo === hi) return sorted[lo];
  const w = idx - lo;
  return sorted[lo] * (1 - w) + sorted[hi] * w;
}

/**
 * Scale cap for Δ→color (legacy): avoids a lone outlier max squashing siblings.
 */
export function heatmapScaleCap(entries: UrlTokenHeatmapEntry[]): number {
  const abs = entries
    .map((e) => Math.abs(e.xgb_predictive_delta))
    .filter((x) => Number.isFinite(x));
  if (abs.length === 0) return 0.02;
  const sorted = [...abs].sort((a, b) => a - b);
  const maxAbs = sorted[sorted.length - 1];
  if (maxAbs < 1e-8) return 0.02;

  const p75 = percentileSorted(sorted, 0.75);
  const p90 = percentileSorted(sorted, 0.9);
  const robust = Math.max(p90, p75 * 1.25, maxAbs * 0.42);
  return Math.max(0.006, Math.min(maxAbs, robust), 1e-4);
}

/**
 * Legacy diverging heatmap when `ui_signals` or fusion weights are missing.
 */
export function heatmapSpanStyleLegacy(
  entry: UrlTokenHeatmapEntry,
  scaleCap: number,
): { backgroundColor: string; color?: string } {
  const cap = Math.max(scaleCap, 1e-4);
  const ratio = entry.xgb_predictive_delta / cap;
  const tDelta = clamp11(
    Math.sign(ratio) * Math.pow(Math.min(1, Math.abs(ratio)), 0.52) * 1.08,
  );

  const ns = clamp01((entry.semantic_similarity + 1) / 2);
  const tSem = clamp11((ns - 0.5) * 2);
  const wSem = clamp01(1 - Math.min(1, Math.abs(tDelta) * 2.2));
  const t = clamp11(tDelta + tSem * wSem * 0.62);

  if (t <= 0) {
    return NEUTRAL_SPAN_STYLE;
  }

  const pseudoRamp = 0.35 + Math.pow(t, 0.7) * 0.65;
  return intensityToUnifiedHeatmapStyles(pseudoRamp);
}

export function heatmapSpanStyleForUrlToken(
  entry: UrlTokenHeatmapEntry,
  fusion: UrlHeatmapFusionWeights | undefined,
  scaleCap: number,
  mode: HeatmapBranchMode = "url",
  batchMaxFused?: number,
): { backgroundColor: string; color?: string } {
  if (entry.ui_signals && fusion) {
    const score = computeUnifiedSegmentIntensity(
      entry.ui_signals,
      fusion,
      mode,
    );
    const cap =
      batchMaxFused !== undefined && batchMaxFused > 0
        ? batchMaxFused
        : Math.max(score, 1e-6);
    const displayRamp = fusedScoreToDisplayRamp(score, cap);
    return intensityToUnifiedHeatmapStyles(displayRamp);
  }
  return heatmapSpanStyleLegacy(entry, scaleCap);
}

/** @deprecated Use heatmapSpanStyleForUrlToken; kept for older tests importing this name */
export function heatmapSpanStyle(
  entry: UrlTokenHeatmapEntry,
  scaleCap: number,
): { backgroundColor: string; color?: string } {
  return heatmapSpanStyleLegacy(entry, scaleCap);
}

export function maxAbsDelta(entries: UrlTokenHeatmapEntry[]): number {
  if (entries.length === 0) return 1e-4;
  return Math.max(
    1e-4,
    ...entries.map((e) => Math.abs(e.xgb_predictive_delta)),
  );
}
