import { APP_CONFIG } from "@lib/config/app";

function base(): string {
  return APP_CONFIG.api.baseUrl.replace(/\/$/, "");
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${base()}${path}`, {
    headers: { Accept: "application/json" },
    credentials: "include",
  });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

/* ── Detection Trend ── */
export type TrendPoint = {
  date: string;
  total_count: number;
  text: number;
  image: number;
  url: number;
  qr: number;
};

export type DetectionTrendResponse = {
  days: number;
  risk_level: string;
  input_types: string[];
  points: TrendPoint[];
};

export type TrendDays = 7 | 30;
export type TrendRiskLevel = "all" | "low" | "medium" | "high";
export type TrendInputType = "text" | "image" | "url" | "qr";

export function fetchDetectionTrend(
  days: TrendDays = 7,
  risk_level: TrendRiskLevel = "all",
  input_types: TrendInputType[] = [],
): Promise<DetectionTrendResponse> {
  const qs = new URLSearchParams({
    days: String(days),
    risk_level,
  });
  input_types.forEach((t) => qs.append("input_types", t));
  return getJson(`/v1/stats/detection-trend?${qs.toString()}`);
}

/* ── Input Type Distribution ── */
export type InputTypeDistribution = {
  text_count: number;
  image_count: number;
  url_count: number;
  qr_count: number;
  total: number;
};

export function fetchInputTypeDistribution(): Promise<InputTypeDistribution> {
  return getJson("/v1/stats/input-type-distribution");
}

/* ── Risk Level Distribution ── */
export type RiskLevelDistribution = {
  low_count: number;
  medium_count: number;
  high_count: number;
  unknown_count: number;
  total: number;
};

export function fetchRiskLevelDistribution(): Promise<RiskLevelDistribution> {
  return getJson("/v1/stats/risk-level-distribution");
}

/* ── Scan Type Ranking ── */
export type ScamTypeRankItem = {
  scam_type: string;
  count: number;
  rank: number;
};

export type ScanTypeRankingResponse = {
  total_cases: number;
  items: ScamTypeRankItem[];
};

/** GET /api/v1/stats/scam-type-ranking — `top_n` in 1…50 (e.g. 3 for top 3). */
export function fetchScanTypeRanking(
  top_n = 3,
): Promise<ScanTypeRankingResponse> {
  return getJson(`/v1/stats/scam-type-ranking?top_n=${top_n}`);
}
